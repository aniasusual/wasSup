"""
Anomaly Detection Node (Phase 5 - V5)

Detects simple anomalies in the current result set by comparing observed
metrics to baselines (AAA) where available, and by leveraging temporal
spike information from V1.

Produces:
  - anomalies: [{ type, value, baseline?, note }]
  - Appends a concise summary to analysis and tool_results.v5_anomaly
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class AnomalyDetectionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AnomalyDetectionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            anomalies: List[Dict[str, Any]] = []

            perf = state.get("performance_metrics") or {}
            temporal = state.get("temporal_trends") or {}

            # Compare performance metrics to baselines when available
            try:
                project_id = state.get("project_id") or ""
                baselines = await project_architecture_service.get_performance_baselines(project_id) if project_id else []
            except Exception:
                baselines = []

            # Aggregate a coarse baseline across services if present
            agg_baseline = None
            if baselines:
                # simple average of p95 and error_rate when provided
                p95_vals = [b.get("p95_latency_ms") for b in baselines if isinstance(b.get("p95_latency_ms"), (int, float))]
                err_vals = [b.get("error_rate_pct") for b in baselines if isinstance(b.get("error_rate_pct"), (int, float))]
                agg_baseline = {
                    "p95_ms": (sum(p95_vals) / len(p95_vals)) if p95_vals else None,
                    "error_rate_pct": (sum(err_vals) / len(err_vals)) if err_vals else None,
                }

            # Heuristic thresholds
            p95_obs = perf.get("p95_ms")
            err_obs = perf.get("error_rate_pct")
            if agg_baseline:
                p95_base = agg_baseline.get("p95_ms")
                if isinstance(p95_obs, (int, float)) and isinstance(p95_base, (int, float)):
                    if p95_obs > p95_base * 1.7 and (p95_obs - p95_base) > 200:  # 70% higher and +200ms absolute
                        anomalies.append({
                            "type": "latency",
                            "value": p95_obs,
                            "baseline": p95_base,
                            "note": "p95 latency significantly above baseline"
                        })
                err_base = agg_baseline.get("error_rate_pct")
                if isinstance(err_obs, (int, float)) and isinstance(err_base, (int, float)):
                    if err_obs > err_base * 1.5 and (err_obs - err_base) > 2.0:
                        anomalies.append({
                            "type": "error_rate",
                            "value": err_obs,
                            "baseline": err_base,
                            "note": "error rate significantly above baseline"
                        })

            # Temporal spikes signal
            spikes = (temporal.get("spikes") or []) if isinstance(temporal, dict) else []
            if spikes:
                anomalies.append({
                    "type": "temporal_spike",
                    "value": len(spikes),
                    "note": "significant hourly spikes detected"
                })

            # Update analysis text
            lines: List[str] = ["", "SECTION: Anomaly Detection"]
            if anomalies:
                for a in anomalies[:5]:
                    base_txt = f" vs baseline {a['baseline']}" if a.get("baseline") is not None else ""
                    lines.append(
                        f"  - Anomaly type={a['type']} value={a['value']}{base_txt} note={a.get('note','')}"
                    )
            else:
                lines.append("  - Outcome: anomalies not detected")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({"v5_anomaly": {"count": len(anomalies)}})
            updated.update({
                "current_step": "anomaly_detection_complete",
                "analysis": new_analysis,
                "anomalies": anomalies,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"AnomalyDetectionNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "anomaly_detection_error",
                "error": f"Anomaly detection failed: {e}",
            })
            return updated
