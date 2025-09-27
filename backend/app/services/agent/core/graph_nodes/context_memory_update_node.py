"""
Context Memory Update Node (Phase 10 - NN)

Aggregates investigation artifacts into the agent's context memory so
future sessions can reuse prior knowledge.
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


class ContextMemoryUpdateNode:
    """Persist investigation outcomes into the shared context memory."""

    MAX_MEMORY_ENTRIES = 50

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ContextMemoryUpdateNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id")
            timestamp = datetime.utcnow().isoformat()

            memory: Dict[str, Any] = dict(state.get("context_memory") or {})
            entries: List[Dict[str, Any]] = list(memory.get("entries") or [])
            stats: Dict[str, Any] = dict(memory.get("stats") or {
                "total_investigations": 0,
                "successful_investigations": 0,
                "by_result_quality": {},
                "by_confidence_level": {},
                "recent_services": [],
                "avg_confidence": 0.0,
                "success_rate": 0.0,
            })

            evidence = state.get("evidence_package") or {}
            timeline = state.get("timeline_summary") or {}
            impact = state.get("impact_analysis") or {}
            formatted = state.get("formatted_response") or {}
            confidence = state.get("investigation_confidence") or {}
            result_quality = state.get("result_quality") or (state.get("tool_results") or {}).get("response_analysis", {}).get("quality")

            services = evidence.get("metadata", {}).get("services") or []
            anomalies = state.get("anomalies") or []
            recommendations = state.get("actionable_recommendations") or []
            followups = state.get("auto_followup_investigations") or []
            performance_metrics = state.get("performance_metrics") or {}

            tags: Set[str] = set()
            if result_quality:
                tags.add(f"quality:{result_quality}")
            confidence_level = (confidence.get("level") or "unknown").lower()
            tags.add(f"confidence:{confidence_level}")
            for anomaly in anomalies:
                atype = str(anomaly.get("type") or "").lower()
                if atype:
                    tags.add(f"anomaly:{atype}")
            risk_level = (state.get("cascade_forecast") or {}).get("risk_level")
            if risk_level:
                tags.add(f"risk:{risk_level}")
            for svc in services:
                tags.add(f"service:{svc}")

            memory_entry = {
                "id": timestamp,
                "timestamp": timestamp,
                "project_id": project_id,
                "user_id": state.get("user_id"),
                "question": state.get("question"),
                "summary": formatted.get("summary") or evidence.get("summary") or state.get("context_summary"),
                "services": services,
                "confidence": confidence,
                "result_quality": result_quality or "unknown",
                "anomaly_count": len(anomalies),
                "recommendation_count": len(recommendations),
                "followup_count": len(followups),
                "timeline": {
                    "start": timeline.get("start"),
                    "end": timeline.get("end"),
                    "event_count": len(timeline.get("events", [])),
                },
                "impact": impact,
                "performance": {
                    "p95_ms": performance_metrics.get("p95_ms"),
                    "error_rate_pct": performance_metrics.get("error_rate_pct"),
                },
                "tags": sorted(tags),
            }

            entries.append(memory_entry)
            if len(entries) > self.MAX_MEMORY_ENTRIES:
                entries = entries[-self.MAX_MEMORY_ENTRIES:]

            total_before = stats.get("total_investigations", 0)
            stats["total_investigations"] = total_before + 1

            quality_bucket = memory_entry["result_quality"]
            quality_counts = stats.setdefault("by_result_quality", {})
            quality_counts[quality_bucket] = quality_counts.get(quality_bucket, 0) + 1

            conf_bucket = confidence_level
            conf_counts = stats.setdefault("by_confidence_level", {})
            conf_counts[conf_bucket] = conf_counts.get(conf_bucket, 0) + 1

            if conf_bucket == "high":
                stats["successful_investigations"] = stats.get("successful_investigations", 0) + 1

            confidence_score = confidence.get("score")
            if confidence_score is not None:
                running_avg = stats.get("avg_confidence", 0.0)
                stats["avg_confidence"] = round(
                    ((running_avg * total_before) + float(confidence_score)) / max(1, total_before + 1),
                    4,
                )

            if stats["total_investigations"]:
                stats["success_rate"] = round(
                    stats.get("successful_investigations", 0) / stats["total_investigations"],
                    4,
                )

            service_counter = Counter()
            for entry in entries:
                for svc in entry.get("services") or []:
                    service_counter[svc] += 1
            stats["recent_services"] = [svc for svc, _ in service_counter.most_common(10)]

            memory["entries"] = entries
            memory["stats"] = stats
            memory["last_updated_at"] = timestamp

            lines = [
                "",
                "SECTION: Context Memory Update",
                f"  - Entry ID: {memory_entry['id']}",
                f"  - Services recorded: {len(memory_entry['services'])}",
                f"  - Result quality: {memory_entry['result_quality']}",
                f"  - Confidence level: {confidence_level.upper()}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "context_memory_updated",
                "analysis": new_analysis,
                "context_memory": memory,
                "context_memory_entry": memory_entry,
                "context_memory_entry_id": memory_entry["id"],
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {"context_memory": memory},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Context memory persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ContextMemoryUpdateNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "context_memory_update_error",
                "error": f"Context memory update failed: {exc}",
            })
            return updated
