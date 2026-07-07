"""Schemas for triage data."""

from typing import Optional


class Ticket:
    def __init__(self, text: str, category: Optional[str] = None):
        self.text = text
        self.category = category
