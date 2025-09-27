"""
Cascade Failure Prediction Node (Phase 9 - JJ)

Estimates potential cascading failures based on critical path, impact,
and dependency metadata.
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


class CascadeFailurePredictionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CascadeFailurePredictionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            critical = state.get("critical_path_summary") or {}
            impact = state.get("impact_analysis") or {}

            forecast = self._predict(critical, impact)

            analysis_lines = [
                "",
                "NODE JJ | Cascade Failure Prediction",
                "  -----------------------------------",
                f"  - Risk level: {forecast.get('risk_level', 'unknown').upper()}",
                f"  - Services at risk: {len(forecast.get('services_at_risk', []))}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "cascade_prediction_complete",
                "analysis": new_analysis,
                "cascade_forecast": forecast,
                "cascade_predicted_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"CascadeFailurePredictionNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "cascade_prediction_error",
                "error": f"Cascade failure prediction failed: {exc}",
            })
            return updated

    def _predict(self, critical: Dict[str, Any], impact: Dict[str, Any]) -> Dict[str, Any]:
        services = critical.get("services") or []
        downstream = critical.get("downstream") or []
        total_services = impact.get("service_count", 0)

        risk_score = len(downstream) + total_services * 0.2
        if impact.get("severity") == "high":
            risk_score += 2

        if risk_score >= 5:
            level = "high"
        elif risk_score >= 3:
            level = "medium"
        else:
            level = "low"

        services_at_risk = downstream[:5] if downstream else services[:5]

        return {
            "risk_level": level,
            "risk_score": round(risk_score, 2),
            "services_at_risk": services_at_risk,
            "notes": "Predicted using dependency downstream coverage and incident severity",
        }

