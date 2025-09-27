"""
Drill-Down Investigation Node (Phase 11 - RR)

Prepares the state for a deeper architecture-aware investigation loop.
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


class DrillDownInvestigationNode:
    """Prime the agent for a drill-down investigation request."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DrillDownInvestigationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            investigation_context = dict(state.get("investigation_context") or {})
            next_steps = list(investigation_context.get("next_steps") or [])
            next_steps.append("Perform architecture-aware drill down")
            investigation_context["next_steps"] = next_steps
            investigation_context["current_focus"] = "drill_down"
            if "confidence_level" in investigation_context:
                investigation_context["confidence_level"] = max(
                    float(investigation_context.get("confidence_level") or 0.0), 0.4
                )

            lines = [
                "",
                "SECTION: Drill-Down Preparation",
                "  - Escalating to architecture-aware decomposition stage",
            ]

            tool_results = dict(state.get("tool_results") or {})
            drill_info = {
                "requested_at": datetime.utcnow().isoformat(),
                "reason": state.get("user_feedback", {}).get("comment"),
            }
            tool_results["drill_down_request"] = drill_info

            updated = state.copy()
            updated.update({
                "current_step": "drill_down_prepared",
                "analysis": (state.get("analysis") or "") + "\n" + "\n".join(lines),
                "investigation_context": investigation_context,
                "query_type": "complex",
                "needs_clarification": False,
                "drill_down_requested": True,
                "tool_results": tool_results,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"DrillDownInvestigationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "drill_down_error",
                "error": f"Drill-down preparation failed: {exc}",
            })
            return updated
