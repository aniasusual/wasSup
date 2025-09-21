"""
Performance Metrics Extraction Node (Phase 5 - V3)

Computes basic performance metrics from the current result set:
- Latency percentiles (p50, p95, p99) when http.latency is present
- Throughput (entries per minute) over the observed time span
- Error rate (based on severity or http status >= 400)

Optionally references performance baselines (AAA) for future comparison.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


_LAT_RE = re.compile(r"^(?P<val>[0-9]*\.?[0-9]+)s$")


def _parse_latency_ms(lat: Any) -> Optional[float]:
    """Parse http latency string like '0.123s' into milliseconds."""
    if not lat:
        return None
    s = str(lat).strip()
    m = _LAT_RE.match(s)
    if not m:
        return None
    try:
        sec = float(m.group("val"))
        return sec * 1000.0
    except Exception:
        return None


def _percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    vals = sorted(values)
    k = (len(vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    if f == c:
        return vals[int(k)]
    d0 = vals[f] * (c - k)
    d1 = vals[c] * (k - f)
    return d0 + d1


def _parse_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        t = ts
        if t.endswith('Z'):
            t = t[:-1] + '+00:00'
        return datetime.fromisoformat(t)
    except Exception:
        return None


class PerformanceMetricsNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PerformanceMetricsNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            total = len(logs)

            # Collect latencies and timestamps
            lats: List[float] = []
            first_ts: Optional[datetime] = None
            last_ts: Optional[datetime] = None
            error_count = 0
            for e in logs:
                http = e.get("http") or {}
                lat = _parse_latency_ms(http.get("latency"))
                if lat is not None:
                    lats.append(lat)
                # Track timestamps
                ts = _parse_ts(e.get("timestamp") or e.get("receiveTimestamp"))
                if ts:
                    if first_ts is None or ts < first_ts:
                        first_ts = ts
                    if last_ts is None or ts > last_ts:
                        last_ts = ts
                # Error counting
                sev = str(e.get("severity") or "").upper()
                st = (http.get("status") if isinstance(http, dict) else None)
                if sev in {"ERROR", "CRITICAL", "ALERT", "EMERGENCY"}:
                    error_count += 1
                elif isinstance(st, int) and st >= 400:
                    error_count += 1

            # Percentiles
            p50 = _percentile(lats, 0.50)
            p95 = _percentile(lats, 0.95)
            p99 = _percentile(lats, 0.99)

            # Throughput (entries per minute)
            throughput = None
            if first_ts and last_ts and last_ts > first_ts:
                minutes = max(1e-6, (last_ts - first_ts).total_seconds() / 60.0)
                throughput = total / minutes

            err_rate = (error_count / total * 100.0) if total else 0.0

            metrics = {
                "p50_ms": round(p50, 2) if p50 is not None else None,
                "p95_ms": round(p95, 2) if p95 is not None else None,
                "p99_ms": round(p99, 2) if p99 is not None else None,
                "throughput_per_min": round(throughput, 2) if throughput is not None else None,
                "error_rate_pct": round(err_rate, 2),
                "samples": len(lats),
            }

            # Baseline context (count only; detailed comparison can be added later)
            try:
                project_id = state.get("project_id") or ""
                baselines = await project_architecture_service.get_performance_baselines(project_id) if project_id else []
                baseline_note = f" | baselines: {len(baselines)}" if baselines else ""
            except Exception:
                baseline_note = ""

            # Append to analysis
            lines: List[str] = ["", "SECTION: Performance Metrics"]
            if metrics["p95_ms"] is not None or metrics["p50_ms"] is not None:
                lines.append(
                    f"  - Latency: p50={metrics['p50_ms'] or 'NA'}ms | p95={metrics['p95_ms'] or 'NA'}ms | p99={metrics['p99_ms'] or 'NA'}ms"
                )
            if metrics["throughput_per_min"] is not None:
                lines.append(f"  - Throughput: {metrics['throughput_per_min']} entries_per_min")
            lines.append(f"  - Error rate: {metrics['error_rate_pct']:.2f}%")
            lines.append(f"  - Entries with latency: {metrics['samples']}{baseline_note}")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({"v3_performance": metrics})
            updated.update({
                "current_step": "performance_metrics_extracted",
                "analysis": new_analysis,
                "performance_metrics": metrics,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"PerformanceMetricsNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "performance_metrics_error",
                "error": f"Performance metrics extraction failed: {e}",
            })
            return updated
