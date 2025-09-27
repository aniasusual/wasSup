"""
Recommendation Engine Node (Phase 12 - VVV)

Consolidates recommendations for presentation and monitoring.
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


class RecommendationEngineNode:
    """Summarise recommendations for downstream presentation."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RecommendationEngineNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            recommendations: List[Dict[str, Any]] = state.get("actionable_recommendations") or []
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "bundle_count": len(recommendations),
            }

            lines = [
                "",
                "SECTION: Recommendation Engine",
                f"  - Recommendation bundles: {summary['bundle_count']}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "recommendation_engine_complete",
                "analysis": new_analysis,
                "recommendation_summary": summary,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"RecommendationEngineNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "recommendation_engine_error",
                "error": f"Recommendation engine failed: {exc}",
            })
            return updated
