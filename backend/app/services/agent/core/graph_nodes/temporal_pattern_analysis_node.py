"""
Temporal Pattern Analysis Node (Phase 5 - V1)

Analyzes time-based trends in the current result set and highlights
spikes or unusual density windows. Optionally references performance
baselines (AAA) for additional context.

Outputs:
  - temporal_trends: { bins: [{hour,count}], spikes: [{hour,count,zscore}] }
  - Appends a concise summary to analysis and tool_results.v1_temporal
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


def _parse_hour(ts: Optional[str]) -> Optional[str]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        t = ts
        if t.endswith('Z'):
            t = t[:-1] + '+00:00'
        dt = datetime.fromisoformat(t)
        return dt.strftime('%Y-%m-%d %H:00')
    except Exception:
        return None


class TemporalPatternAnalysisNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.TemporalPatternAnalysisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            total = len(logs)

            # Build hourly histogram
            hourly: Dict[str, int] = {}
            for e in logs:
                hour_key = _parse_hour(e.get("timestamp") or e.get("receiveTimestamp"))
                if hour_key:
                    hourly[hour_key] = hourly.get(hour_key, 0) + 1

            # Compute simple spikes using z-score (mean + 2*std)
            bins = sorted(hourly.items(), key=lambda kv: kv[0])
            counts = [c for _, c in bins]
            spikes: List[Dict[str, Any]] = []
            if counts:
                mean = sum(counts) / len(counts)
                var = sum((c - mean) ** 2 for c in counts) / len(counts)
                std = var ** 0.5
                threshold = mean + 2 * std
                for h, c in bins:
                    if std > 0 and c >= threshold:
                        z = (c - mean) / std
                        spikes.append({"hour": h, "count": c, "zscore": round(z, 2)})

            temporal_trends = {
                "bins": [{"hour": h, "count": c} for h, c in bins],
                "spikes": spikes,
                "total": total,
            }

            # Optionally fetch baselines for context (not strictly used for detection now)
            try:
                project_id = state.get("project_id") or ""
                baselines = await project_architecture_service.get_performance_baselines(project_id) if project_id else []
                baseline_note = f" | baselines: {len(baselines)}" if baselines else ""
            except Exception:
                baseline_note = ""

            # Update analysis text
            lines: List[str] = ["", "SECTION: Temporal Pattern Analysis"]
            if bins:
                top = ", ".join([f"{h}:{c}" for h, c in sorted(hourly.items(), key=lambda kv: (-kv[1], kv[0]))[:5]])
                lines.append(f"  - Top density hours: {top}")
            if spikes:
                s = ", ".join([f"{s['hour']} (x{s['count']}, z={s['zscore']})" for s in spikes])
                lines.append(f"  - Spikes: {s}")
            else:
                lines.append("  - Outcome: significant spikes not detected")
            lines.append(f"  - Entries analyzed: {total}{baseline_note}")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({"v1_temporal": {"spike_count": len(spikes), "bin_count": len(bins)}})
            updated.update({
                "current_step": "temporal_pattern_analyzed",
                "analysis": new_analysis,
                "temporal_trends": temporal_trends,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"TemporalPatternAnalysisNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "temporal_pattern_analysis_error",
                "error": f"Temporal analysis failed: {e}",
            })
            return updated
