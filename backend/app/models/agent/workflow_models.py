"""
Workflow models for the LangGraph agent system.

This module defines the core state management and workflow models
for the intelligent GCP log investigation agent.
"""

from typing import Dict, List, Optional, Any, TypedDict, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class QueryInput(BaseModel):
    """
    User query input model with validation and preprocessing.
    
    This represents the raw user input before processing by the agent.
    """
    question: str = Field(..., description="The user's question or query")
    project_id: str = Field(..., description="GCP project ID")
    session_id: Optional[str] = Field(None, description="Existing session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User identifier")
    services: Optional[List[str]] = Field(None, description="Specific GCP services to investigate")
    time_range: Optional[Dict[str, str]] = Field(None, description="Time range for log analysis")
    collection: Optional[str] = Field(None, description="Specific log collection or resource")
    limit: int = Field(1000, description="Maximum number of logs to retrieve", ge=1, le=10000)
    access_token: Optional[str] = Field(None, description="GCP access token for API calls")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Show me authentication errors from cloud_run_revision services in the last hour",
                "project_id": "my-gcp-project",
                "services": ["cloud_run_revision"],
                "time_range": {
                    "start_time": "2024-01-15T10:00:00Z",
                    "end_time": "2024-01-15T11:00:00Z"
                },
                "limit": 1000
            }
        }


class InvestigationContext(BaseModel):
    """
    Context information for the current investigation.
    
    This tracks the investigation state and accumulated knowledge.
    """
    investigation_id: str = Field(..., description="Unique identifier for this investigation")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="When investigation started")
    current_focus: str = Field("", description="Current area of investigation focus")
    evidence_collected: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence gathered so far")
    hypotheses: List[str] = Field(default_factory=list, description="Current hypotheses being tested")
    confidence_level: float = Field(0.0, description="Confidence in current findings", ge=0.0, le=1.0)
    next_steps: List[str] = Field(default_factory=list, description="Planned next steps")
    
    class Config:
        json_schema_extra = {
            "example": {
                "investigation_id": "inv_12345",
                "current_focus": "Authentication failures in cloud_run_revision",
                "evidence_collected": [
                    {"type": "log_analysis", "summary": "Found 15 auth errors", "timestamp": "2024-01-15T10:30:00Z"}
                ],
                "hypotheses": ["Token expiration issue", "Permission misconfiguration"],
                "confidence_level": 0.7,
                "next_steps": ["Check IAM policies", "Verify token validity"]
            }
        }


class AgentState(TypedDict):
    """
    Core state object for the LangGraph agent workflow.
    
    This TypedDict defines the persistent state that flows through
    all nodes in the agent workflow graph.
    """
    # User inputs
    question: str
    project_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    services: Optional[List[str]]
    time_range: Optional[Dict[str, str]]
    collection: Optional[str]
    limit: int
    access_token: Optional[str]
    
    # Agent workflow state
    current_step: str
    needs_clarification: bool
    missing_info: List[str]
    investigation_context: InvestigationContext
    
    # Results and outputs
    analysis: str
    tool_results: Optional[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    relevant_logs: List[Dict[str, Any]]
    clarifying_questions: List[Dict[str, str]]
    
    # Conversation management
    conversation_history: List[Dict[str, Any]]
    context_summary: str
    error: Optional[str]
    
    # Query processing state
    query_type: Optional[Literal["simple", "complex", "ambiguous"]]
    extracted_entities: Dict[str, Any]
    processed_question: str
    
    # API interaction state
    api_calls_made: int
    last_api_call_time: Optional[datetime]
    rate_limit_info: Optional[Dict[str, Any]]
    
    # Learning and memory
    discovered_patterns: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    architecture_insights: Dict[str, Any]


class NodeResult(BaseModel):
    """
    Standard result format for LangGraph nodes.
    
    This provides a consistent interface for node outputs
    and enables proper error handling and logging.
    """
    success: bool = Field(..., description="Whether the node execution was successful")
    message: str = Field("", description="Human-readable message about the result")
    data: Optional[Dict[str, Any]] = Field(None, description="Node-specific output data")
    next_step: Optional[str] = Field(None, description="Suggested next step in workflow")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[float] = Field(None, description="Time taken to execute in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Query input processed successfully",
                "data": {
                    "query_type": "simple",
                    "extracted_entities": {"services": ["cloud_run_revision"], "severity": ["ERROR"]}
                },
                "next_step": "intent_classification",
                "execution_time": 0.15
            }
        }


class WorkflowConfig(BaseModel):
    """
    Configuration for the agent workflow.
    
    This allows runtime configuration of the agent behavior
    without code changes.
    """
    max_api_calls_per_session: int = Field(50, description="Maximum API calls allowed per session")
    max_investigation_time_minutes: int = Field(30, description="Maximum time for a single investigation")
    confidence_threshold: float = Field(0.7, description="Minimum confidence for proceeding without clarification")
    enable_streaming: bool = Field(True, description="Whether to enable real-time streaming responses")
    enable_learning: bool = Field(True, description="Whether to enable pattern learning and memory")
    debug_mode: bool = Field(False, description="Enable detailed logging and debugging")
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_api_calls_per_session": 50,
                "max_investigation_time_minutes": 30,
                "confidence_threshold": 0.7,
                "enable_streaming": True,
                "enable_learning": True,
                "debug_mode": False
            }
        }
