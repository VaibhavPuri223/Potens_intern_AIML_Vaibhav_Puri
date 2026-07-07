"""
Structured output contracts for the triage agent.

Every agent decision is validated against TriageOutput before it is written
to disk or shown to the user. This is what prevents "silent magic" -- if the
LLM returns something that doesn't fit the contract, pydantic raises instead
of us silently accepting garbage.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field

Category = Literal[
    "Billing",
    "Technical Issue",
    "Account & Access",
    "Feature Request",
    "Complaint & Escalation",
    "General Inquiry",
]

Priority = Literal["P0", "P1", "P2"]

NextTool = Literal[
    "kb_lookup",
    "similar_ticket_search",
    "draft_acknowledgment",
    "human_escalation",
    "none",
]


class TraceStep(BaseModel):
    """One step in the agent's visible reasoning trace."""
    step: int
    thought: str = Field(default="", description="Model's reasoning/commentary at this step")
    tool_call: Optional[dict] = Field(default=None, description="{name, arguments} if a tool was called")
    tool_result: Optional[Any] = Field(default=None, description="Real return value from the tool function")


class TriageOutput(BaseModel):
    """Final structured decision returned by the agent."""
    category: Category
    priority: Priority
    next_tool: NextTool
    reasoning: str = Field(description="Full reasoning trace in prose, for humans reviewing the ticket")
    why: str = Field(description="One-paragraph plain-English justification, no jargon")
    confidence: float = Field(ge=0.0, le=1.0)
    trace: list[TraceStep] = Field(default_factory=list)

    class Config:
        extra = "forbid"
