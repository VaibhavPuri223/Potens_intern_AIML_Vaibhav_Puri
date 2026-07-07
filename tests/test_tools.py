"""
Unit tests for the real tool functions. These do NOT require an API key --
they test the pure Python functions in src/tools.py directly.

Run with:
    pytest tests/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import kb_lookup, similar_ticket_search, draft_acknowledgment, human_escalation


def test_kb_lookup_finds_known_issue():
    result = kb_lookup("I was charged twice for my subscription")
    assert result["found"] is True
    assert result["kb_id"] == "KB-001"


def test_kb_lookup_no_match():
    result = kb_lookup("completely unrelated made up gibberish query xyz123")
    assert result["found"] is False


def test_kb_lookup_detects_outage():
    result = kb_lookup("getting a 500 error on checkout")
    assert result["found"] is True
    assert result["is_known_outage"] is True


def test_similar_ticket_search_finds_matches():
    result = similar_ticket_search("service down outage third time this month")
    assert result["count"] >= 1
    assert result["recurring_pattern_detected"] in (True, False)


def test_similar_ticket_search_no_matches():
    result = similar_ticket_search("zzz completely unrelated query about nothing")
    assert result["count"] == 0
    assert result["recurring_pattern_detected"] is False


def test_draft_acknowledgment_p0_urgency():
    result = draft_acknowledgment("Technical Issue", "P0", "Alex")
    assert "within the hour" in result["draft"]
    assert "Alex" in result["draft"]


def test_draft_acknowledgment_p2_urgency():
    result = draft_acknowledgment("General Inquiry", "P2")
    assert "1-2 business days" in result["draft"]


def test_human_escalation_returns_ticket_id():
    result = human_escalation("low confidence", "ambiguous garbled ticket")
    assert result["status"] == "queued_for_human_review"
    assert "escalation_id" in result
