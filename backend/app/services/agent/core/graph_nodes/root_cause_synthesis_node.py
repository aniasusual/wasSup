"""
Root Cause Synthesis Node (Phase 7 - DD)

Condenses the collected evidence into a concise root cause narrative
with recommended remediation actions for high-confidence outcomes.
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


class RootCauseSynthesisNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RootCauseSynthesisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            resource_insights: List[Dict[str, Any]] = state.get("resource_correlation_insights") or []
            chain_insights: List[Dict[str, Any]] = state.get("dependency_chain_insights") or []

            synthesis = self._build_synthesis(bundle, resource_insights, chain_insights)
            recommendations = self._build_recommendations(bundle)

            analysis_lines = [
                "",
                "NODE DD | Root Cause Synthesis",
                "  -------------------------------",
                f"  - Root cause identified: {synthesis.get('primary_cause', 'Unknown')}",
                f"  - Confidence: {synthesis.get('confidence', '—')}",
            ]
            if recommendations:
                analysis_lines.append(f"  - Recommendations prepared: {len(recommendations)}")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "root_cause_synthesis_complete",
                "analysis": new_analysis,
                "root_cause_summary": synthesis,
                "recommended_actions": recommendations,
                "root_cause_generated_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"RootCauseSynthesisNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "root_cause_synthesis_error",
                "error": f"Root cause synthesis failed: {exc}",
            })
            return updated

    def _build_synthesis(
        self,
        bundle: Dict[str, Any],
        resource_insights: List[Dict[str, Any]],
        chain_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        key_findings = bundle.get("key_findings") or []
        services = bundle.get("services_in_focus") or []

        primary_cause = key_findings[0] if key_findings else (
            f"Service {services[0]} shows dominant anomalies" if services else "Insufficient data"
        )

        hottest_resource = None
        if resource_insights:
            hottest_resource = max(resource_insights, key=lambda item: item.get("confidence", 0))
        critical_chain = None
        if chain_insights:
            critical_chain = max(chain_insights, key=lambda item: item.get("impact_score", 0))

        return {
            "primary_cause": primary_cause,
            "supporting_evidence": key_findings[:4],
            "critical_resource": hottest_resource,
            "critical_chain": critical_chain,
            "confidence": bundle.get("confidence", {}).get("level") or bundle.get("confidence", {}).get("score") or "high",
        }

    def _build_recommendations(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = bundle.get("recommended_actions") or []
        if isinstance(actions, list) and actions:
            formatted = []
            for idx, action in enumerate(actions[:4], start=1):
                formatted.append({
                    "id": f"rec_{idx}",
                    "description": action,
                })
            return formatted

        related_paths = bundle.get("related_paths") or []
        if related_paths:
            return [{
                "id": "rec_paths",
                "description": "Validate traffic along critical dependency paths for residual impact",
            }]

        return [{
            "id": "rec_default",
            "description": "Confirm remediation plan with service owners and schedule follow-up monitoring",
        }]

