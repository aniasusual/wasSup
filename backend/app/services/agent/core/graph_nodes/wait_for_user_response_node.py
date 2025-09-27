"""
Wait For User Response Node (Phase 8 - H)

Captures the state when awaiting user clarification and stores the
pending questions for client-side rendering.
"""

import logging
from datetime import datetime
from typing import Any, Dict

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class WaitForUserResponseNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.WaitForUserResponseNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            questions = list(state.get("clarifying_questions") or [])
            analysis_lines = [
                "",
                "NODE H | Wait For User Response",
                "  --------------------------------",
                f"  - Pending questions: {len(questions)}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "awaiting_user_response",
                "analysis": new_analysis,
                "needs_clarification": True,
                "last_clarification_prompt_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"WaitForUserResponseNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "wait_for_user_response_error",
                "error": f"Failed to enter wait state: {exc}",
            })
            return updated

