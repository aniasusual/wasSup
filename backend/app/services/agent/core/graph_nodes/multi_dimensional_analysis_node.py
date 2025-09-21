"""
Multi-Dimensional Log Analysis Node (Phase 3 - V, basic)

Performs simple, multi-angle analysis over the fetched logs to enrich the
analysis text and provide structured summary for the UI. This basic
implementation focuses on:

- Temporal density (by hour)
- Error/Warning rates
- HTTP status distribution
- Top recurring messages (compact preview)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


def _parse_hour(ts: Optional[str]) -> Optional[str]:
    if not ts or not isinstance(ts, str):
        return None
    # Expect RFC3339 / ISO strings; normalize to hour key YYYY-MM-DD HH
    try:
        # handle possible Z or offset
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        dt = datetime.fromisoformat(ts)
        return dt.strftime('%Y-%m-%d %H:00')
    except Exception:
        return None


class MultiDimensionalAnalysisNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.MultiDimensionalAnalysisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            total = len(logs)

            # Temporal density by hour (basic)
            hourly: Dict[str, int] = {}
            for e in logs:
                hour_key = _parse_hour(e.get("timestamp") or e.get("receiveTimestamp"))
                if hour_key:
                    hourly[hour_key] = hourly.get(hour_key, 0) + 1
            top_hours = sorted(hourly.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

            # Error / Warning rates
            error_set = {"ERROR", "CRITICAL", "ALERT", "EMERGENCY"}
            warn_set = {"WARNING"}
            err = 0
            warn = 0
            for e in logs:
                sev = str(e.get("severity") or "").upper()
                if sev in error_set:
                    err += 1
                elif sev in warn_set:
                    warn += 1
            error_rate = (err / total) * 100.0 if total else 0.0
            warn_rate = (warn / total) * 100.0 if total else 0.0

            # HTTP status distribution (basic)
            status_counts: Dict[str, int] = {}
            for e in logs:
                http = e.get("http") or {}
                st = http.get("status")
                if st is None:
                    continue
                key = str(st)
                status_counts[key] = status_counts.get(key, 0) + 1
            top_status = sorted(status_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

            # Top recurring messages (compact)
            msg_counts: Dict[str, int] = {}
            for e in logs:
                m = e.get("message")
                if not m:
                    continue
                key = str(m)[:200]  # compact key to avoid massive texts
                msg_counts[key] = msg_counts.get(key, 0) + 1
            top_msgs = sorted(msg_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]

            md_summary = {
                "top_hours": [{"hour": k, "count": v} for k, v in top_hours],
                "error_rate": round(error_rate, 2),
                "warning_rate": round(warn_rate, 2),
                "top_status": [{"status": k, "count": v} for k, v in top_status],
                "top_messages": [{"message": k, "count": v} for k, v in top_msgs],
                "total": total,
            }

            # Append to analysis text
            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Multi-Dimensional Analysis"]
            lines.append(f"  - Entries analyzed: {total}")
            if top_hours:
                dens = ", ".join([f"{h['hour']}:{h['count']}" for h in md_summary["top_hours"]])
                lines.append(f"  - Temporal density top: {dens}")
            lines.append(
                f"  - Error rate: {md_summary['error_rate']:.2f}% | Warning rate: {md_summary['warning_rate']:.2f}%"
            )
            if top_status:
                sts = ", ".join([f"{s['status']}:{s['count']}" for s in md_summary["top_status"]])
                lines.append(f"  - HTTP status top: {sts}")
            if top_msgs:
                msgs = "; ".join([f"{m['message']} (x{m['count']})" for m in md_summary["top_messages"]])
                lines.append(f"  - Top messages: {msgs}")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({"md_analysis": md_summary})
            updated.update({
                "current_step": "md_analysis_basic",
                "analysis": new_analysis,
                "md_summary": md_summary,
                "tool_results": tr,
            })
            self.logger.info("Multi-dimensional analysis complete")
            return updated
        except Exception as e:
            self.logger.error(f"MultiDimensionalAnalysisNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "md_analysis_error",
                "error": f"Multi-dimensional analysis failed: {e}",
            })
            return updated
