"""
Critical Path Identification Node (Phase 9 - II)

Determines the most critical service chain contributing to the incident
based on dependency insights and impact metrics.
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


class CriticalPathIdentificationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CriticalPathIdentificationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            chains: List[Dict[str, Any]] = state.get("dependency_chain_insights") or []
            impact: Dict[str, Any] = state.get("impact_analysis") or {}

            critical = self._select_critical_path(chains, impact)

            analysis_lines = [
                "",
                "NODE II | Critical Path Identification",
                "  -------------------------------------",
                f"  - Critical path services: {len(critical.get('services', []))}",
                f"  - Impact score: {critical.get('impact_score', 'n/a')}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "critical_path_identified",
                "analysis": new_analysis,
                "critical_path_summary": critical,
                "critical_path_identified_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"CriticalPathIdentificationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "critical_path_identification_error",
                "error": f"Critical path identification failed: {exc}",
            })
            return updated

    def _select_critical_path(self, chains: List[Dict[str, Any]], impact: Dict[str, Any]) -> Dict[str, Any]:
        if not chains:
            services = impact.get("services") or []
            return {
                "services": services,
                "impact_score": impact.get("service_count", 0),
                "notes": "Derived from impact service list",
            }

        top = max(chains, key=lambda item: item.get("impact_score", 0))
        return {
            "services": top.get("critical_paths", {}).get("downstream") or top.get("services") or [],
            "impact_score": top.get("impact_score"),
            "upstream": top.get("critical_paths", {}).get("upstream"),
            "downstream": top.get("critical_paths", {}).get("downstream"),
        }

