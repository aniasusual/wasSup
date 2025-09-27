"""
Correlation Engine Node (Phase 12 - SSS)

Aggregates correlation signals before automated follow-ups.
"""

import logging
from datetime import datetime
from typing import Any, Dict

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class CorrelationEngineNode:
    """Summarise correlation triggers for LangGraph agent orchestration."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CorrelationEngineNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            triggers = state.get("cross_service_triggers") or []
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "trigger_count": len(triggers),
                "high_priority": len([t for t in triggers if (t.get("priority") or "").lower() == "high"]),
            }

            lines = [
                "",
                "SECTION: Correlation Engine",
                f"  - Triggers generated: {summary['trigger_count']}",
                f"  - High priority: {summary['high_priority']}",
            ]

            new_analysis = (state.get("analysis") or "")
            updated = state.copy()
            updated.update({
                "current_step": "correlation_engine_complete",
                "analysis": (new_analysis + "\n" + "\n".join(lines)).strip(),
                "correlation_engine_summary": summary,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"CorrelationEngineNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "correlation_engine_error",
                "error": f"Correlation engine failed: {exc}",
            })
            return updated
