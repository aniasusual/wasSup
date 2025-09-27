"""
Performance Optimization Node (Phase 13 - HHHH)

Summarises performance optimisation hints from API execution.
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


class PerformanceOptimizationNode:
    """Collect performance optimisation statistics post API calls."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PerformanceOptimizationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "api_calls": state.get("api_calls_made", 0),
                "last_call": state.get("last_api_call_time"),
            }

            lines = [
                "",
                "SECTION: Performance Optimization",
                f"  - API calls made: {stats['api_calls']}",
            ]

            updated = state.copy()
            updated.update({
                "current_step": "performance_optimization_complete",
                "analysis": ((state.get("analysis") or "") + "\n" + "\n".join(lines)).strip(),
                "performance_optimization_summary": stats,
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"PerformanceOptimizationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "performance_optimization_error",
                "error": f"Performance optimization metrics failed: {exc}",
            })
            return updated
