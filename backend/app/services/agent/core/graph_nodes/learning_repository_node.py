"""
Learning Repository Node (Phase 10 - FFF)

Collects discovered patterns and insights to expand the learning
repository for future investigations.
"""

import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Set

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class LearningRepositoryNode:
    MAX_REPOSITORY_ENTRIES = 150

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.LearningRepositoryNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id")
            timestamp = datetime.utcnow().isoformat()

            repository: List[Dict[str, Any]] = list(state.get("learning_repository") or [])
            evidence = state.get("evidence_package") or {}
            key_findings = evidence.get("key_findings") or []
            cascade = state.get("cascade_forecast") or {}
            anomalies = state.get("anomalies") or []
            resource_insights = state.get("resource_correlation_insights") or []
            correlation_findings = state.get("correlation_findings") or []
            temporal_trends = state.get("temporal_trends") or {}
            confidence = state.get("investigation_confidence") or {}
            result_quality = state.get("result_quality") or (state.get("tool_results") or {}).get("response_analysis", {}).get("quality")

            services = evidence.get("metadata", {}).get("services") or []
            tags: Set[str] = {f"quality:{result_quality}" if result_quality else "", f"risk:{cascade.get('risk_level')}" if cascade.get("risk_level") else ""}
            tags.discard("")
            for anomaly in anomalies:
                atype = str(anomaly.get("type") or "").lower()
                if atype:
                    tags.add(f"anomaly:{atype}")

            learning_entry = {
                "timestamp": timestamp,
                "project_id": project_id,
                "services": services,
                "key_findings": key_findings[:5],
                "cascade_risk": cascade.get("risk_level"),
                "confidence": confidence,
                "result_quality": result_quality,
                "signals": {
                    "anomalies": [a.get("type") for a in anomalies if a.get("type")],
                    "resource_hotspots": [c.get("service") for c in resource_insights if c.get("service")][:5],
                    "correlation_types": [f.get("type") for f in correlation_findings if f.get("type")][:5],
                    "temporal_spikes": len(temporal_trends.get("spikes") or []),
                },
                "tags": sorted(tags),
            }

            repository.append(learning_entry)
            if len(repository) > self.MAX_REPOSITORY_ENTRIES:
                repository = repository[-self.MAX_REPOSITORY_ENTRIES:]

            # Build repository summary for downstream consumers
            tag_counter = Counter()
            service_counter = Counter()
            confidence_sum = 0.0
            confidence_count = 0
            for item in repository:
                for tag in item.get("tags") or []:
                    tag_counter[tag] += 1
                for svc in item.get("services") or []:
                    service_counter[svc] += 1
                score = ((item.get("confidence") or {}).get("score"))
                if isinstance(score, (int, float)):
                    confidence_sum += float(score)
                    confidence_count += 1

            summary = {
                "total_entries": len(repository),
                "top_tags": [tag for tag, _ in tag_counter.most_common(10)],
                "top_services": [svc for svc, _ in service_counter.most_common(10)],
                "average_confidence": round(confidence_sum / confidence_count, 4) if confidence_count else 0.0,
                "last_updated_at": timestamp,
            }

            lines = [
                "",
                "SECTION: Learning Repository",
                f"  - Entries stored: {summary['total_entries']}",
                f"  - Top tag: {summary['top_tags'][0] if summary['top_tags'] else 'n/a'}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "learning_repository_updated",
                "analysis": new_analysis,
                "learning_repository": repository,
                "learning_repository_summary": summary,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {
                            "learning_repository": repository,
                            "learning_repository_summary": summary,
                        },
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Learning repository persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"LearningRepositoryNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "learning_repository_error",
                "error": f"Learning repository update failed: {exc}",
            })
            return updated
