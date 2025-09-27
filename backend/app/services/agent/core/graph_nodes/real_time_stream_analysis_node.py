"""
Real-Time Stream Analysis Node (Phase 13 - CCCC)

Summarises streaming insights from the current evidence for live dashboards.
"""

import logging
from datetime import datetime
from typing import Any, Dict

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


class RealTimeStreamAnalysisNode:
    """Generate real-time stream analytics summary."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RealTimeStreamAnalysisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            evidence = state.get("evidence_bundle") or {}
            timeline = state.get("timeline_summary") or {}
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "services": len(evidence.get("services_in_focus") or []),
                "events": len(timeline.get("events") or []),
            }

            lines = [
                "",
                "SECTION: Real-Time Stream Analysis",
                f"  - Active services: {summary['services']}",
                f"  - Timeline events: {summary['events']}",
            ]

            updated = state.copy()
            updated.update({
                "current_step": "real_time_stream_complete",
                "analysis": ((state.get("analysis") or "") + "\n" + "\n".join(lines)).strip(),
                "real_time_stream_summary": summary,
            })

            if self.config.enable_learning and state.get("project_id"):
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        state.get("project_id"),
                        {"real_time_stream_summary": summary},
                    )
                except Exception as persist_err:  # pragma: no cover
                    self.logger.warning(f"Real-time stream summary persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"RealTimeStreamAnalysisNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "real_time_stream_error",
                "error": f"Real-time stream analysis failed: {exc}",
            })
            return updated
