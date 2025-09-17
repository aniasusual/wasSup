"""
Session Complete Node - Phase 1, Step UU of the investigation workflow.

Marks the session as ready for the next query and records a light
session summary into the state. This is a basic, in-memory step that
does not persist to a database (Phase 1 scope).
"""

import logging
from datetime import datetime
from typing import Dict, Any

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class SessionCompleteNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SessionCompleteNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            # Build a lightweight summary for this session
            summary_parts = []
            if state.get("query_type"):
                summary_parts.append(f"Type: {state['query_type']}")
            if state.get("needs_clarification"):
                summary_parts.append("Clarification requested")
            if state.get("architecture_context"):
                ctx = state["architecture_context"] or {}
                if ctx.get("context_summary"):
                    summary_parts.append(ctx["context_summary"])

            session_summary = " | ".join(summary_parts) if summary_parts else "Session complete"

            # Append a small record to conversation history (in-memory)
            history_entry: Dict[str, Any] = {
                "role": "system",
                "content": "Session ready for next query",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "summary": session_summary,
                    "query_type": state.get("query_type"),
                    "needs_clarification": state.get("needs_clarification", False),
                }
            }

            conversation_history = list(state.get("conversation_history") or [])
            conversation_history.append(history_entry)

            updated = state.copy()
            updated.update({
                "current_step": "session_complete",
                "conversation_history": conversation_history,
                "session_status": "ready",
                "session_ready_at": datetime.utcnow().isoformat(),
                "context_summary": session_summary,
            })

            self.logger.info("Session marked complete and ready for next query")
            return updated
        except Exception as e:
            self.logger.error(f"Error in SessionCompleteNode: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "session_complete_error",
                "error": f"Session completion failed: {e}",
            })
            return updated

