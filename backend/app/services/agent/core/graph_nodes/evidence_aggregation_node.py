"""
Evidence Aggregation Engine (Phase 6 - Y)

Aggregates findings from the Phase 6 nodes into a structured evidence
bundle that powers the final presentation and confidence assessment.
"""

import logging
from typing import Any, Dict, List

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class EvidenceAggregationNode:
    """Aggregates evidence and computes confidence (graph node Y)."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.EvidenceAggregationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            triggers = list(state.get("cross_service_triggers") or [])
            followups = list(state.get("auto_followup_investigations") or [])
            chains = list(state.get("dependency_chain_insights") or [])
            infra = state.get("infrastructure_impact") or {}
            resources = list(state.get("resource_correlation_insights") or [])
            correlation_findings = list(state.get("correlation_findings") or [])
            anomalies = list(state.get("anomalies") or [])
            error_clusters = list(state.get("error_clusters") or [])
            temporal = state.get("temporal_trends") or {}

            services: List[str] = []
            for trigger in triggers:
                svc = trigger.get("service")
                if svc:
                    services.append(svc)
            for insight in chains:
                svc = insight.get("service")
                if svc:
                    services.append(svc)
                services.extend([s for s in insight.get("upstream", []) if s])
                services.extend([s for s in insight.get("downstream", []) if s])
            for corr in resources:
                if corr.get("service"):
                    services.append(corr.get("service"))

            services_in_focus = list(dict.fromkeys([s for s in services if isinstance(s, str)]))

            high_priority = any(t.get("priority") == "high" for t in triggers)
            score = 0.2 * len(services_in_focus)
            if high_priority:
                score += 0.5
            if correlation_findings:
                score += 0.3
            if resources:
                score += 0.2
            if anomalies:
                score += 0.2
            if error_clusters:
                score += 0.1
            score = round(min(0.99, score), 2)

            if score >= 0.75:
                level = "high"
            elif score >= 0.45:
                level = "medium"
            else:
                level = "low"

            key_findings: List[str] = []
            for trigger in triggers[:3]:
                svc = trigger.get("service") or "unknown"
                key_findings.append(
                    f"{svc}: {trigger.get('priority', 'n/a')} priority via {', '.join(trigger.get('signals')[:2])}"
                )
            if anomalies:
                anomaly_types = sorted({a.get("type") for a in anomalies if a.get("type")})
                if anomaly_types:
                    key_findings.append(f"Detected anomalies: {', '.join(anomaly_types)}")
            shared = infra.get("shared") or {}
            if shared.get("clusters"):
                key_findings.append(f"Shared clusters impacted: {', '.join(shared['clusters'][:2])}")

            recommended_actions = [
                f"{f.get('service') or 'global'} → {f.get('action')}"
                for f in followups[:4]
            ]

            spikes = [s for s in (temporal.get("spikes") or []) if isinstance(s, dict)]
            timeline = [
                {"hour": s.get("hour"), "count": s.get("count")}
                for s in spikes[:4]
                if s.get("hour")
            ]

            related_paths = [
                finding.get("services")
                for finding in correlation_findings
                if finding.get("type") == "flow_path_correlation"
            ][:3]

            evidence_bundle = {
                "services_in_focus": services_in_focus,
                "confidence": {"score": score, "level": level},
                "key_findings": key_findings,
                "recommended_actions": recommended_actions,
                "timeline": timeline,
                "related_paths": related_paths,
                "supporting_data": {
                    "triggers": len(triggers),
                    "followups": len(followups),
                    "anomalies": len(anomalies),
                    "error_clusters": len(error_clusters),
                    "resource_correlations": len(resources),
                },
                "infrastructure_summary": infra.get("summary"),
            }

            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Evidence Aggregation"]
            lines.append(f"  - Services in focus: {len(services_in_focus)}")
            lines.append(f"  - Confidence level: {level} (score {score:.2f})")
            if recommended_actions:
                lines.append(f"  - Recommended actions: {', '.join(recommended_actions[:2])}")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = dict(updated.get("tool_results") or {})
            tr.update({
                "phase6_evidence": {
                    "confidence_level": level,
                    "service_count": len(services_in_focus),
                }
            })
            updated.update({
                "current_step": "evidence_aggregation_complete",
                "analysis": new_analysis,
                "evidence_bundle": evidence_bundle,
                "investigation_confidence": evidence_bundle["confidence"],
                "tool_results": tr,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"EvidenceAggregationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "evidence_aggregation_error",
                "error": f"Evidence aggregation failed: {exc}",
            })
            return updated
