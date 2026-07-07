"""
The triage agent's orchestration loop.

This is the actual agentic loop: the LLM decides which tool(s) to call,
we execute the *real* Python function, feed the real result back to the
model, and let it decide whether it needs another tool call or is ready
to produce a final structured decision. Every step is captured in `trace`
so the full reasoning is visible, not just the final answer.
"""

import json
import re
from .llm_client import client, MODEL
from .tools import TOOL_SCHEMAS, TOOL_FUNCS
from .schemas import TriageOutput, TraceStep

SYSTEM_PROMPT = """You are a support ticket triage agent for a SaaS product.

You MUST use the available tools to gather real evidence before deciding:
- Call kb_lookup to check if this matches a known issue.
- Call similar_ticket_search to check if this is a recurring pattern (recurring
  issues should generally be treated as higher priority than a one-off).
- Once you have decided on category + priority, call draft_acknowledgment to
  produce the actual customer-facing message.
Do not skip tool calls and guess when a tool could verify your assumption.

Categories (choose exactly one):
- Billing: charges, refunds, invoices, payment failures
- Technical Issue: bugs, errors, crashes, outages
- Account & Access: login, password, permissions, lockouts
- Feature Request: "can you add / support..."
- Complaint & Escalation: angry customer, churn threat, repeated unresolved issue, legal/PR risk
- General Inquiry: how-to questions, documentation, pricing questions

Priorities:
- P0: data loss, security breach, full outage, legal threat, enterprise customer fully blocked -> respond <1hr
- P1: feature broken for a paying customer, billing charged incorrectly, angry customer threatening churn -> respond 4-8hr
- P2: general questions, feature requests, cosmetic bugs -> respond 1-2 business days

If, after using the tools, your confidence in the classification is below 0.55,
call human_escalation instead of guessing, and reflect that in next_tool.

When you are done gathering evidence, respond with ONLY a single JSON object
(no markdown fences, no commentary before or after) matching exactly this shape:
{
  "category": "<one of the six categories above>",
  "priority": "P0 | P1 | P2",
  "next_tool": "kb_lookup | similar_ticket_search | draft_acknowledgment | human_escalation | none",
  "reasoning": "<full explanation of how you reached this decision, referencing what the tools returned>",
  "why": "<one plain-English paragraph a non-technical reviewer could read>",
  "confidence": <float between 0 and 1>
}
"""


def _extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object even if the model wraps it
    in markdown fences or adds stray text around it."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)
    return json.loads(text)


def run_triage(ticket_text: str, metadata: dict | None = None, max_iterations: int = 6) -> dict:
    """Run one ticket through the agent loop and return a validated,
    JSON-serializable TriageOutput dict, including the full trace."""
    metadata = metadata or {}
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ticket: {ticket_text}\nMetadata: {json.dumps(metadata)}"},
    ]

    trace: list[TraceStep] = []
    final_json = None

    for step in range(1, max_iterations + 1):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg.model_dump(exclude_none=True))
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                fn = TOOL_FUNCS.get(fn_name)
                result = fn(**fn_args) if fn else {"error": f"unknown tool {fn_name}"}

                trace.append(TraceStep(
                    step=step,
                    thought=msg.content or f"Decided to call {fn_name} with {fn_args}",
                    tool_call={"name": fn_name, "arguments": fn_args},
                    tool_result=result,
                ))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })
            continue  # let the model see tool results and decide next step

        # No tool call: the model should be giving its final decision now
        trace.append(TraceStep(step=step, thought=msg.content or ""))
        try:
            final_json = _extract_json(msg.content or "")
        except (json.JSONDecodeError, TypeError):
            final_json = {
                "category": "General Inquiry",
                "priority": "P2",
                "next_tool": "none",
                "reasoning": f"Model did not return valid JSON. Raw output: {msg.content!r}",
                "why": "Fell back to a safe default because the model's final response could not be parsed.",
                "confidence": 0.3,
            }
        break

    if final_json is None:
        final_json = {
            "category": "General Inquiry",
            "priority": "P2",
            "next_tool": "human_escalation",
            "reasoning": "Agent exceeded max iterations without producing a final decision.",
            "why": "Escalating to a human because the agent could not converge on a decision.",
            "confidence": 0.2,
        }

    output = TriageOutput(**final_json, trace=trace)
    return output.model_dump()
