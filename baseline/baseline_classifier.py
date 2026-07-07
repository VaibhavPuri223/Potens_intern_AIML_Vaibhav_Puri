"""
STRETCH GOAL (Q2): baseline single-prompt classifier, no tools.

Same model, same output schema as the agent, but this version gets a
single prompt and must classify from the raw ticket text alone -- it has
no access to the knowledge base or past-ticket history. Run this against
the same 10-12 examples as the real agent to show, side by side, what
tool calling actually buys you.

Usage:
    python -m baseline.baseline_classifier
"""

import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.llm_client import client, MODEL  # noqa: E402

BASELINE_PROMPT = """You are a support ticket triage classifier. You have NO tools
and NO access to any knowledge base or ticket history -- classify using only the
text of the ticket below.

Categories: Billing, Technical Issue, Account & Access, Feature Request,
Complaint & Escalation, General Inquiry.
Priorities: P0 (critical, <1hr), P1 (high, 4-8hr), P2 (normal, 1-2 days).

Respond with ONLY a JSON object, no markdown fences, no extra text:
{
  "category": "...",
  "priority": "...",
  "reasoning": "...",
  "why": "...",
  "confidence": 0.0
}

Ticket: {ticket_text}
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)
    return json.loads(text)


def classify_baseline(ticket_text: str) -> dict:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": BASELINE_PROMPT.format(ticket_text=ticket_text)}],
        temperature=0.2,
    )
    content = resp.choices[0].message.content
    try:
        return _extract_json(content)
    except (json.JSONDecodeError, TypeError):
        return {
            "category": "General Inquiry",
            "priority": "P2",
            "reasoning": f"Could not parse model output: {content!r}",
            "why": "Fell back to a safe default.",
            "confidence": 0.3,
        }


def main():
    inputs = json.loads((Path(__file__).parent.parent / "examples" / "inputs.json").read_text())
    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(exist_ok=True)

    results = []
    for ex in inputs:
        result = classify_baseline(ex["text"])
        result["id"] = ex["id"]
        results.append(result)
        (out_dir / f"baseline_{ex['id']:02d}.json").write_text(json.dumps(result, indent=2))
        print(f"[{ex['id']:02d}] {ex['text'][:50]!r} -> {result.get('category')} / {result.get('priority')}")

    print(f"\nDone. Wrote {len(results)} baseline outputs to {out_dir}/")


if __name__ == "__main__":
    main()
