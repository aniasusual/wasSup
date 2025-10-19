from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, ConfigDict


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


class ChatTurnRequest(BaseModel):
    """Request payload for a chat turn."""
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    project_id: str = Field(..., description="GCP project ID")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context including architectureSummary and other metadata"
    )



class ChatMessageResponse(BaseModel):
    """Serialized chat message returned to the frontend."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    status: str = "sent"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ChatTurnResponseModel(BaseModel):
    """Response shape for a single chat turn."""

    session_id: str = Field(alias="sessionId")
    reply: ChatMessageResponse
    plan: Optional[Dict[str, Any]] = None
    follow_up_questions: List[str] = Field(default_factory=list, alias="followUpQuestions")
    context_summary: str = Field(default="", alias="contextSummary")
    query_analysis: Optional[Dict[str, Any]] = Field(default=None, alias="queryAnalysis")
    query_history: List[Dict[str, Any]] = Field(default_factory=list, alias="queryHistory")

    model_config = ConfigDict(populate_by_name=True)


class ChatSessionSummaryResponse(BaseModel):
    """Lightweight session details for listing sessions."""

    session_id: str = Field(alias="sessionId")
    title: str
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    last_message_preview: Optional[str] = Field(default=None, alias="lastMessagePreview")

    model_config = ConfigDict(populate_by_name=True)


class ChatSessionDetailResponse(BaseModel):
    """Full session payload with message history."""

    session_id: str = Field(alias="sessionId")
    title: str
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    messages: List[ChatMessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

