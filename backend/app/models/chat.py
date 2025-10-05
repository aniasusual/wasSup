from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class InvestigationStep(BaseModel):
    """Single step in the orchestrator's investigation plan."""

    id: str
    title: str
    description: str
    status: Literal["pending", "in_progress", "complete"] = "pending"


class InvestigationPlan(BaseModel):
    """Structured plan returned by the orchestrator stub."""

    focus: str
    summary: str
    steps: List[InvestigationStep] = Field(default_factory=list)
    suggested_queries: List[str] = Field(default_factory=list)


class QueryIntent(BaseModel):
    description: str
    confidence: float = 0.5
    service_hints: List[str] = Field(default_factory=list)


class FilterSuggestion(BaseModel):
    key: str
    value: str
    confidence: float = 0.5


class QueryUnderstandingResult(BaseModel):
    summary: Optional[str] = None
    intents: List[QueryIntent] = Field(default_factory=list)
    clarifying_questions: List[str] = Field(default_factory=list)
    filter_suggestions: List[FilterSuggestion] = Field(default_factory=list)


class ChatMessagePayload(BaseModel):
    """Message payload shared with the frontend chat client."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class LogReferenceMetadata(BaseModel):
    """Metadata about a log reference."""
    service: Optional[str] = None
    severity: Optional[str] = None
    count: Optional[int] = None
    time_range: Optional[str] = None


class LogReference(BaseModel):
    """
    A reference to a set of logs that can be fetched on-demand.
    The frontend will create a button for each log reference.
    """
    id: str = Field(..., description="Unique identifier for this log reference")
    description: str = Field(..., description="Human-readable description for the button label")
    filter: str = Field(..., description="Cloud Logging API filter string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (service, severity, count, etc.)")
    preview: List[str] = Field(default_factory=list, description="Preview of 1-3 log entries")


class ChatTurnRequest(BaseModel):
    """Request payload for a chat turn."""
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    project_id: str = Field(..., description="GCP project ID")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context including architectureSummary and other metadata"
    )


class ChatTurnResponse(BaseModel):
    """Response from the agent after analyzing logs."""
    session_id: str
    reply: str = Field(..., description="The agent's analysis and findings (cleaned text without log dumps)")
    log_references: List[LogReference] = Field(
        default_factory=list,
        description="Structured references to relevant logs for on-demand viewing"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response (model, timestamp, etc.)"
    )


class LogFetchRequest(BaseModel):
    """Request to fetch logs using a filter."""
    project_id: str
    filter_str: str
    order_by: str = "timestamp desc"
    page_size: int = Field(default=100, le=1000)
    page_token: Optional[str] = None

