"""
Actionable Recommendations Generation Node (Phase 9 - LL)

Transforms evidence into prioritized remediation steps for various time
scales.
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


class ActionableRecommendationsNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ActionableRecommendationsNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            evidence_package = state.get("evidence_package") or {}
            cascade = state.get("cascade_forecast") or {}

            recommendations = self._generate_recommendations(evidence_package, cascade)

            analysis_lines = [
                "",
                "NODE LL | Actionable Recommendations",
                "  -----------------------------------",
                f"  - Recommendation bundles: {len(recommendations)}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "recommendations_generated",
                "analysis": new_analysis,
                "actionable_recommendations": recommendations,
                "recommendations_generated_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ActionableRecommendationsNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "recommendations_generation_error",
                "error": f"Recommendation generation failed: {exc}",
            })
            return updated

    def _generate_recommendations(self, evidence: Dict[str, Any], cascade: Dict[str, Any]) -> List[Dict[str, Any]]:
        key_findings = evidence.get("key_findings") or []
        services = evidence.get("metadata", {}).get("services") or []
        risk_level = cascade.get("risk_level")

        bundles: List[Dict[str, Any]] = []

        if key_findings:
            bundles.append({
                "priority": "immediate",
                "actions": [f"Mitigate root cause: {key_findings[0]}"] + [f"Verify remediation for {svc}" for svc in services[:2]],
            })

        bundles.append({
            "priority": "short_term",
            "actions": [
                "Add focused monitoring on critical path services",
                "Schedule follow-up validation run after remediation",
            ],
        })

        if risk_level == "high":
            bundles.append({
                "priority": "escalation",
                "actions": [
                    "Notify incident response leadership",
                    "Prepare rollback/containment plan for dependent services",
                ],
            })

        bundles.append({
            "priority": "long_term",
            "actions": [
                "Document learnings in shared knowledge base",
                "Review architecture for resilience improvements",
            ],
        })

        return bundles

