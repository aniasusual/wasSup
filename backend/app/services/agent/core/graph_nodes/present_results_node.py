"""
Present Results Node (Phase 2 - PP)

Formats and prepares the fetched results for presentation to the user.
This node does not fetch data; it summarizes `relevant_logs` and updates
the analysis text and lightweight presentation metadata for the UI.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class PresentResultsNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PresentResultsNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            entries: List[Dict[str, Any]] = state.get("relevant_logs") or []

            total = len(entries)
            severities: Dict[str, int] = {}
            sample: List[Dict[str, Any]] = []
            for i, e in enumerate(entries[:5]):
                sev = (e.get("severity") or "UNKNOWN").upper()
                severities[sev] = severities.get(sev, 0) + 1
                sample.append({
                    "timestamp": e.get("timestamp"),
                    "severity": e.get("severity"),
                    "message": e.get("message"),
                    "resource_type": e.get("resource_type"),
                })
            for e in entries[5:]:
                sev = (e.get("severity") or "UNKNOWN").upper()
                severities[sev] = severities.get(sev, 0) + 1

            sev_parts = [f"{k}:{v}" for k, v in sorted(severities.items(), key=lambda kv: (-kv[1], kv[0]))]
            summary_line = f"Returned {total} entries" + (f" | Severities: {', '.join(sev_parts)}" if sev_parts else "")

            analysis = state.get("analysis") or ""
            new_analysis_blocks = [
                "\n## 📊 Results Summary",
                summary_line,
            ]
            new_analysis = (analysis + "\n" + "\n".join(new_analysis_blocks)).strip()

            presentation = {
                "total": total,
                "severity_breakdown": severities,
                "sample": sample,
                "generated_at": datetime.utcnow().isoformat(),
            }

            updated = state.copy()
            updated.update({
                "current_step": "results_presented",
                "analysis": new_analysis,
                "presentation": presentation,
            })
            self.logger.info("Results prepared for presentation")
            return updated
        except Exception as e:
            self.logger.error(f"PresentResultsNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "present_results_error",
                "error": f"Results presentation failed: {e}",
            })
            return updated

