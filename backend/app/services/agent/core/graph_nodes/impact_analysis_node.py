"""
Impact Analysis & Scope Assessment Node (Phase 9 - HH)

Quantifies investigation impact, affected services/users, and scope to
support downstream critical path analysis.
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


class ImpactAnalysisNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ImpactAnalysisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            timeline: Dict[str, Any] = state.get("timeline_summary") or {}
            performance = state.get("performance_metrics") or {}

            impact = self._compute_impact(bundle, timeline, performance)

            analysis_lines = [
                "",
                "NODE HH | Impact Analysis",
                "  ------------------------",
                f"  - Services affected: {impact.get('service_count', 0)}",
                f"  - Estimated user impact: {impact.get('estimated_users', 'n/a')}",
                f"  - Duration (minutes): {impact.get('duration_minutes', 'n/a')}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "impact_analysis_complete",
                "analysis": new_analysis,
                "impact_analysis": impact,
                "impact_assessed_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"ImpactAnalysisNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "impact_analysis_error",
                "error": f"Impact analysis failed: {exc}",
            })
            return updated

    def _compute_impact(
        self,
        bundle: Dict[str, Any],
        timeline: Dict[str, Any],
        performance: Dict[str, Any],
    ) -> Dict[str, Any]:
        services = bundle.get("services_in_focus") or []
        duration_minutes = self._duration_minutes(timeline)
        error_rate = performance.get("error_rate_pct")

        estimated_users = None
        if error_rate is not None and duration_minutes is not None:
            estimated_users = int(max(0, error_rate / 100 * duration_minutes * 50))

        return {
            "service_count": len(services),
            "services": services,
            "duration_minutes": duration_minutes,
            "error_rate_pct": error_rate,
            "estimated_users": estimated_users,
            "severity": bundle.get("confidence", {}).get("level"),
        }

    def _duration_minutes(self, timeline: Dict[str, Any]) -> Any:
        start = timeline.get("start")
        end = timeline.get("end")
        if not (start and end):
            return None
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            span = max(0.0, (end_dt - start_dt).total_seconds() / 60.0)
            return round(span, 2)
        except Exception:
            return None

