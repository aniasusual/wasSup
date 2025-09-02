"""
Agent State Management

Defines the state structure and enums for the LangGraph agent workflow.
"""

from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum


class InvestigationStep(str, Enum):
    """Enumeration of investigation steps in the agent workflow."""
    INTELLIGENT_ANALYSIS = "intelligent_analysis"
    CONTEXT_RETRIEVAL = "context_retrieval"
    LOG_ANALYSIS = "log_analysis"
    SMART_CLARIFICATION = "smart_clarification"
    ACTION_GENERATION = "action_generation"
    COMPLETE = "complete"


class AgentState(TypedDict):
    """State object for the LangGraph agent workflow."""
    
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
    
    # Agent state
    current_step: str
    needs_clarification: bool
    missing_info: List[str]
    investigation_context: Dict[str, Any]
    conversation_context: Dict[str, Any]
    
    # Results
    analysis: str
    tool_results: Optional[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    relevant_logs: List[Dict[str, Any]]
    clarifying_questions: List[Dict[str, str]]
    
    # Conversation
    conversation_history: List[Dict[str, Any]]
    context_summary: str
    error: Optional[str]


class LogEntry:
    """Structured representation of a GCP log entry."""
    
    def __init__(self, raw_entry: Dict[str, Any], project_id: str):
        self.raw_entry = raw_entry
        self.project_id = project_id
        self._parse_entry()
    
    def _parse_entry(self):
        """Parse the raw log entry into structured fields."""
        entry = self.raw_entry
        
        # Core identification
        self.id = entry.get("insertId") or f"entry_{id(self)}"
        self.insert_id = entry.get("insertId")
        self.timestamp = entry.get("timestamp")
        self.severity = str(entry.get("severity", "DEFAULT"))
        
        # Message extraction
        self.message = self._extract_message(entry)
        
        # Resource information
        self.resource = self._extract_resource(entry)
        
        # Log metadata
        self.labels = dict(entry.get("labels", {})) if isinstance(entry.get("labels"), dict) else {}
        self.log_name = entry.get("logName")
        
        # Payload data
        self.json_payload = entry.get("jsonPayload") if isinstance(entry.get("jsonPayload"), dict) else None
        self.text_payload = entry.get("textPayload") if isinstance(entry.get("textPayload"), str) else None
        
        # Tracing and request information
        self.http_request = entry.get("httpRequest")
        self.trace_id = entry.get("trace") or entry.get("traceId")
        self.span_id = entry.get("spanId")
        self.operation = entry.get("operation")
        
        # Additional fields
        self.source_location = entry.get("sourceLocation")
        self.metadata = entry.get("metadata")
        self.receive_timestamp = entry.get("receiveTimestamp")
        self.proto_payload = entry.get("protoPayload")
    
    def _extract_message(self, entry: Dict[str, Any]) -> str:
        """Extract message from various payload types."""
        json_payload = entry.get("jsonPayload")
        text_payload = entry.get("textPayload")
        
        if isinstance(json_payload, dict):
            return json_payload.get("message") or json_payload.get("msg") or str(json_payload)
        elif isinstance(text_payload, str):
            return text_payload
        else:
            return str(json_payload or text_payload or "")
    
    def _extract_resource(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract resource information from log entry."""
        resource = entry.get("resource") or {}
        if not isinstance(resource, dict):
            return {"type": "", "labels": {}}
        
        return {
            "type": resource.get("type", ""),
            "labels": dict(resource.get("labels", {})) if isinstance(resource.get("labels"), dict) else {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "id": self.id,
            "insertId": self.insert_id,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "message": self.message,
            "resource": self.resource,
            "labels": self.labels,
            "logName": self.log_name,
            "projectId": self.project_id,
            "jsonPayload": self.json_payload,
            "textPayload": self.text_payload,
            "httpRequest": self.http_request,
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "operation": self.operation,
            "sourceLocation": self.source_location,
            "metadata": self.metadata,
            "receiveTimestamp": self.receive_timestamp,
            "protoPayload": self.proto_payload,
        }
        
        # Remove None values to keep the object clean
        return {k: v for k, v in result.items() if v is not None}
    
    def to_ui_format(self) -> Dict[str, Any]:
        """Convert to UI-friendly format."""
        return {
            "id": str(self.id),
            "insertId": self.insert_id,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "messageSnippet": (self.message or "")[:250],
            "serviceId": self.resource.get("type"),
            "traceId": self.trace_id,
            "score": 0.0,  # Default score
            "completeLog": self.to_dict(),
            "raw": self.to_dict(),
        }
