"""
Execute Additional API Queries Node (Phase 7 - EE)

Forms follow-up API query plans based on generated hypotheses and feeds
them back into the investigation loop for renewed evidence aggregation.
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


class AdditionalApiQueriesNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AdditionalApiQueriesNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            hypotheses: List[Dict[str, Any]] = state.get("generated_hypotheses") or []
            followup_service_seeds = state.get("followup_service_seeds") or []

            plans = self._build_query_plans(hypotheses, followup_service_seeds)

            analysis_lines = [
                "",
                "NODE EE | Additional API Queries",
                "  --------------------------------",
                f"  - Plans created: {len(plans)}",
            ]
            for idx, plan in enumerate(plans[:3], start=1):
                analysis_lines.append(f"  - Plan {idx}: target={plan.get('service')} window={plan.get('time_window')}")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            pending_queries = list(state.get("pending_additional_queries") or [])
            pending_queries.extend(plans)
            iteration_count = int(state.get("low_confidence_iteration") or 0) + 1

            updated = state.copy()
            updated.update({
                "current_step": "additional_api_queries_prepared",
                "analysis": new_analysis,
                "pending_additional_queries": pending_queries,
                "last_additional_query_at": datetime.utcnow().isoformat(),
                "low_confidence_iteration": iteration_count,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"AdditionalApiQueriesNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "additional_api_queries_error",
                "error": f"Additional API query planning failed: {exc}",
            })
            return updated

    def _build_query_plans(
        self,
        hypotheses: List[Dict[str, Any]],
        service_seeds: List[str],
    ) -> List[Dict[str, Any]]:
        plans: List[Dict[str, Any]] = []
        base_services = service_seeds[:]
        for hyp in hypotheses:
            svc = hyp.get("service")
            if svc and svc not in base_services:
                base_services.append(svc)

        for idx, svc in enumerate(base_services[:4], start=1):
            plans.append({
                "id": f"additional_query_{idx}",
                "service": svc,
                "time_window": "PT30M",
                "filters": {
                    "severity": "ERROR",
                    "focus": hyp_match(hypotheses, svc),
                },
            })
        return plans


def hyp_match(hypotheses: List[Dict[str, Any]], service: str) -> str:
    for hyp in hypotheses:
        if hyp.get("service") == service:
            return hyp.get("summary") or "expanded investigation"
    return "expanded investigation"
