"""
Query History & Results Node (Phase 10 - CCC)

Logs investigation metadata to query history for future reference.
"""

import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

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


class QueryHistoryNode:
    MAX_HISTORY_ENTRIES = 200

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.QueryHistoryNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id")
            timestamp = datetime.utcnow().isoformat()

            history: List[Dict[str, Any]] = list(state.get("query_history") or [])
            confidence = state.get("investigation_confidence") or {}
            result_quality = state.get("result_quality") or (state.get("tool_results") or {}).get("response_analysis", {}).get("quality")
            services = (state.get("evidence_package") or {}).get("metadata", {}).get("services", [])
            time_range = state.get("time_range")
            investigation_context = state.get("investigation_context") or {}
            start_time = investigation_context.get("start_time")
            duration_seconds = None
            if isinstance(start_time, datetime):
                duration_seconds = max(0.0, (datetime.utcnow() - start_time).total_seconds())

            history_entry = {
                "timestamp": timestamp,
                "question": state.get("question"),
                "project_id": project_id,
                "session_id": state.get("session_id"),
                "investigation_id": investigation_context.get("investigation_id"),
                "confidence": confidence,
                "result_quality": result_quality or "unknown",
                "services": services,
                "time_range": time_range,
                "clarifications_requested": len(state.get("clarifying_questions") or []),
                "needs_clarification": state.get("needs_clarification", False),
                "duration_seconds": duration_seconds,
            }

            history.append(history_entry)
            if len(history) > self.MAX_HISTORY_ENTRIES:
                history = history[-self.MAX_HISTORY_ENTRIES:]

            # Aggregate statistics for quick reuse
            total_entries = len(history)
            service_counter = Counter()
            quality_counter = Counter()
            confidence_sum = 0.0
            confidence_count = 0
            clarification_total = 0
            for item in history:
                for svc in item.get("services") or []:
                    service_counter[svc] += 1
                quality_counter[item.get("result_quality") or "unknown"] += 1
                score = ((item.get("confidence") or {}).get("score"))
                if isinstance(score, (int, float)):
                    confidence_sum += float(score)
                    confidence_count += 1
                clarification_total += int(item.get("clarifications_requested") or 0)

            history_stats = {
                "total_entries": total_entries,
                "average_confidence": round(confidence_sum / confidence_count, 4) if confidence_count else 0.0,
                "result_quality_breakdown": dict(quality_counter),
                "service_popularity": [svc for svc, _ in service_counter.most_common(10)],
                "clarification_rate": round(clarification_total / max(1, total_entries), 4),
                "last_updated_at": timestamp,
            }

            lines = [
                "",
                "SECTION: Query History",
                f"  - Total investigations tracked: {history_stats['total_entries']}",
                f"  - Average confidence: {history_stats['average_confidence']:.2f}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "query_history_logged",
                "analysis": new_analysis,
                "query_history": history,
                "query_history_stats": history_stats,
                "query_history_entry": history_entry,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {
                            "query_history": history,
                            "query_history_stats": history_stats,
                        },
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Query history persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"QueryHistoryNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "query_history_error",
                "error": f"Query history logging failed: {exc}",
            })
            return updated
