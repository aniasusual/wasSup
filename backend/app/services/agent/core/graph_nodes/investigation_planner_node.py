"""
Investigation Planner Node (Phase 12 - PPP)

Transforms query decomposition into a structured investigation plan.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class InvestigationPlannerNode:
    """Generate investigation plan metadata for LangGraph agent."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.InvestigationPlannerNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            decomposition = state.get("query_decomposition") or {}
            anchors = decomposition.get("anchors") or []
            flow_hint = decomposition.get("flow_hint") or []
            goals = decomposition.get("goals") or []

            plan = {
                "timestamp": datetime.utcnow().isoformat(),
                "anchor_count": len(anchors),
                "flow_length": len(flow_hint),
                "goals": goals[:5],
            }

            lines = [
                "",
                "SECTION: Investigation Planner",
                f"  - Anchors: {plan['anchor_count']}",
                f"  - Flow length: {plan['flow_length']}",
            ]
            if plan["goals"]:
                lines.append(f"  - Goals: {', '.join(plan['goals'])}")

            new_analysis = (state.get("analysis") or "")

            updated = state.copy()
            updated.update({
                "current_step": "investigation_planner_complete",
                "analysis": (new_analysis + "\n" + "\n".join(lines)).strip(),
                "investigation_planner_summary": plan,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"InvestigationPlannerNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "investigation_planner_error",
                "error": f"Investigation planner failed: {exc}",
            })
            return updated
