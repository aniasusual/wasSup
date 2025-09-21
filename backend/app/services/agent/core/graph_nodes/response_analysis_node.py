"""
Response Analysis & Pattern Detection Node (Phase 3 - R, basic)

Computes basic result statistics from the fetched logs and assesses
result quality (too_many, too_few, empty, optimal). Adds a concise
summary into the analysis text and stores structured stats for later
nodes (S/T/U/V).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class ResponseAnalysisNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ResponseAnalysisNode")

        # Thresholds for basic quality assessment (configurable via WorkflowConfig)
        self.desired_min = getattr(getattr(config, 'phase3', object()), 'desired_min', 5)
        self.desired_max = getattr(getattr(config, 'phase3', object()), 'desired_max', 1000)

    def _result_quality(self, total: int) -> str:
        if total == 0:
            return "empty"
        if total < self.desired_min:
            return "too_few"
        if total > self.desired_max:
            return "too_many"
        return "optimal"

    @staticmethod
    def _first_ts(log: Dict[str, Any]) -> Optional[str]:
        ts = log.get("timestamp") or log.get("receiveTimestamp")
        return ts if isinstance(ts, str) else None

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            total = len(logs)

            # Severity counts
            sev_counts: Dict[str, int] = {}
            resource_counts: Dict[str, int] = {}
            first_ts = None
            last_ts = None
            for e in logs:
                sev = str(e.get("severity") or "").upper() or "UNKNOWN"
                sev_counts[sev] = sev_counts.get(sev, 0) + 1
                rtype = e.get("resource_type") or ""
                if rtype:
                    resource_counts[rtype] = resource_counts.get(rtype, 0) + 1
                ts = self._first_ts(e)
                if ts:
                    if not first_ts or ts < first_ts:
                        first_ts = ts
                    if not last_ts or ts > last_ts:
                        last_ts = ts

            # Basic pattern hints: top severities and resource types
            top_sev = sorted(sev_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
            top_rsrc = sorted(resource_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]

            result_stats = {
                "total": total,
                "severity_counts": sev_counts,
                "time_span": {"start": first_ts, "end": last_ts},
                "resource_types": [k for k, _ in top_rsrc],
            }
            quality = self._result_quality(total)
            pattern_hints = {
                "top_severities": [{"severity": k, "count": v} for k, v in top_sev],
                "top_resource_types": [{"type": k, "count": v} for k, v in top_rsrc],
            }

            # Append concise summary to analysis
            analysis = state.get("analysis") or ""
            summary_lines = [
                "",
                "SECTION: Response Summary",
                f"  - Total entries: {total}",
                f"  - Result quality: {quality}",
            ]
            if top_sev:
                sev_txt = ", ".join([f"{x['severity']}:{x['count']}" for x in pattern_hints["top_severities"]])
                summary_lines.append(f"  - Severities: {sev_txt}")
            if first_ts or last_ts:
                summary_lines.append(f"  - Time span: {first_ts or '?'} → {last_ts or '?'}")

            new_analysis = (analysis + "\n" + "\n".join(summary_lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({
                "response_analysis": {"quality": quality, **result_stats}
            })
            updated.update({
                "current_step": "response_analyzed",
                "analysis": new_analysis,
                "result_stats": result_stats,
                "result_quality": quality,
                "pattern_hints": pattern_hints,
                "tool_results": tr,
            })
            self.logger.info("Response analyzed: total=%s quality=%s", total, quality)
            return updated
        except Exception as e:
            self.logger.error(f"ResponseAnalysisNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "response_analysis_error",
                "error": f"Response analysis failed: {e}",
            })
            return updated
