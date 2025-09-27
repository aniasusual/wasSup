"""
Alternative Analysis Path Node (Phase 11 - SS)

Allows the agent to pivot to a different investigative approach.
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


class AlternativeAnalysisPathNode:
    """Reset analysis parameters to explore an alternate path."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AlternativeAnalysisPathNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            investigation_context = dict(state.get("investigation_context") or {})
            investigation_context["current_focus"] = "alternative_path"

            lines = [
                "",
                "SECTION: Alternative Analysis Path",
                "  - Resetting entity extraction for alternative perspective",
            ]

            tool_results = dict(state.get("tool_results") or {})
            tool_results["alternative_path_requests"] = (
                tool_results.get("alternative_path_requests", 0) + 1
            )

            updated = state.copy()
            updated.update({
                "current_step": "alternative_path_prepared",
                "analysis": (state.get("analysis") or "") + "\n" + "\n".join(lines),
                "investigation_context": investigation_context,
                "extracted_entities": {},
                "query_type": None,
                "needs_clarification": False,
                "alternative_path_requested": True,
                "tool_results": tool_results,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"AlternativeAnalysisPathNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "alternative_path_error",
                "error": f"Alternative path preparation failed: {exc}",
            })
            return updated
