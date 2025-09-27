"""
Investigation Confidence Router Node (Phase 7 - AA)

Routes the workflow according to the assessed confidence level while
recording the routing decision for downstream analysis.
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


class ConfidenceDecisionRouterNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ConfidenceDecisionRouterNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            assessment: Dict[str, Any] = state.get("confidence_assessment") or {}
            level = str(assessment.get("level") or state.get("investigation_confidence", {}).get("level") or "unknown").lower()

            route = self._normalize_route(level)
            timestamp = datetime.utcnow().isoformat()

            analysis_lines = [
                "",
                "NODE AA | Confidence Decision Router",
                "  ---------------------------------",
                f"  - Selected route: {route.upper()}",
                f"  - Level basis: {level.upper() if level != 'unknown' else 'UNSPECIFIED'}",
                f"  - Timestamp: {timestamp}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "confidence_router_complete",
                "analysis": new_analysis,
                "confidence_route": route,
                "confidence_route_timestamp": timestamp,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"ConfidenceDecisionRouterNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "confidence_router_error",
                "error": f"Confidence routing failed: {exc}",
                "confidence_route": "medium",
            })
            return updated

    def _normalize_route(self, level: str) -> str:
        if level in {"high", "medium", "low"}:
            return level
        return "medium"

