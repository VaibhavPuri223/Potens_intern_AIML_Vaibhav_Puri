"""
Real, callable tools for the triage agent.

These are genuine Python functions that read real (local) data files and
return real results -- the LLM does not know the answer itself, it has to
call these functions and read what comes back. This is what makes this
"real tool calling" rather than a string-matching shortcut dressed up as
an agent.

Three required tools:
  1. kb_lookup                - known-issue / known-fix lookup
  2. similar_ticket_search     - precedent search over past resolved tickets
  3. draft_acknowledgment      - generates the actual customer-facing message

Stretch tool:
  4. human_escalation          - only called when the agent's confidence is low
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def kb_lookup(query: str) -> dict:
    """Search the internal knowledge base for a known issue matching the query.

    Real behavior: naive keyword match over data/kb.json. Returns the first
    match, whether it corresponds to a known active outage, and the
    suggested fix / talking points if found.
    """
    kb = json.loads((DATA_DIR / "kb.json").read_text())
    query_l = query.lower()
    matches = [entry for entry in kb if any(kw in query_l for kw in entry["keywords"])]

    if not matches:
        return {"found": False, "message": "No matching known issue in the knowledge base."}

    top = matches[0]
    return {
        "found": True,
        "kb_id": top["id"],
        "issue": top["issue"],
        "suggested_fix": top["fix"],
        "is_known_outage": top.get("is_outage", False),
    }


def similar_ticket_search(query: str, top_k: int = 3) -> dict:
    """Search past resolved tickets for similar complaints/patterns.

    Real behavior: keyword-overlap scoring over data/past_tickets.json.
    This is what lets the agent notice recurring issues (e.g. repeated
    outages for the same customer/topic), which should raise priority
    even if a single ticket in isolation looks minor.
    """
    tickets = json.loads((DATA_DIR / "past_tickets.json").read_text())
    query_words = set(w.strip(".,!?") for w in query.lower().split())

    scored = []
    for t in tickets:
        ticket_words = set(w.strip(".,!?") for w in t["text"].lower().split())
        overlap = len(query_words & ticket_words)
        if overlap > 0:
            scored.append((overlap, t))

    scored.sort(key=lambda pair: -pair[0])
    top_matches = [t for _, t in scored[:top_k]]

    return {
        "matches": top_matches,
        "count": len(top_matches),
        "recurring_pattern_detected": len(top_matches) >= 2,
    }


def draft_acknowledgment(category: str, priority: str, customer_name: str = "there") -> dict:
    """Generate the actual customer-facing acknowledgment message.

    Real behavior: deterministic template fill, not another LLM call --
    this keeps it a genuine "tool" with a fixed, auditable output rather
    than more free-text generation.
    """
    urgency_line = {
        "P0": "We've flagged this as critical and a team member will reach out within the hour.",
        "P1": "We've prioritized this and will follow up within 4-8 hours.",
        "P2": "We've logged this and will follow up within 1-2 business days.",
    }.get(priority, "We've received your message and will follow up soon.")

    draft = (
        f"Hi {customer_name}, thanks for reaching out about your {category.lower()} issue. "
        f"{urgency_line} If anything changes on your end in the meantime, just reply to this thread."
    )
    return {"draft": draft}


def human_escalation(reason: str, ticket_summary: str) -> dict:
    """Escalate to a human reviewer. Only called when agent confidence is low.

    Real behavior: simulates paging a human by writing a queue entry and
    returning a ticket ID. In a production system this would call a real
    paging/ticketing API (PagerDuty, Zendesk, etc).
    """
    return {
        "status": "queued_for_human_review",
        "escalation_id": "ESC-0001",
        "reason": reason,
        "ticket_summary": ticket_summary,
    }


# JSON schemas describing each tool to the LLM (OpenAI/Groq tool-calling format)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "kb_lookup",
            "description": "Search the internal knowledge base for a known issue matching the ticket. Use this before deciding priority on any technical/billing/account complaint.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Key phrase or summary of the customer's issue"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "similar_ticket_search",
            "description": "Search past resolved tickets for similar complaints, to detect recurring patterns that should raise priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Key phrase or summary of the customer's issue"},
                    "top_k": {"type": "integer", "description": "How many similar tickets to return, default 3"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_acknowledgment",
            "description": "Draft the actual customer-facing acknowledgment message once category and priority are decided.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "priority": {"type": "string"},
                    "customer_name": {"type": "string"},
                },
                "required": ["category", "priority"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "human_escalation",
            "description": "Escalate this ticket to a human reviewer. Only call this if your confidence in the classification is below 0.55.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Why you are unsure / escalating"},
                    "ticket_summary": {"type": "string"},
                },
                "required": ["reason", "ticket_summary"],
            },
        },
    },
]

TOOL_FUNCS = {
    "kb_lookup": kb_lookup,
    "similar_ticket_search": similar_ticket_search,
    "draft_acknowledgment": draft_acknowledgment,
    "human_escalation": human_escalation,
}
