"""
API Orchestrator Node (Phase 12 - RRR)

Tracks API orchestration metadata prior to execution.
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


class APIOrchestratorNode:
    """Record API request metadata for orchestration layer."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.APIOrchestratorNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            request = state.get("logging_request") or {}
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "page_size": request.get("page_size"),
                "resource_scope": len(request.get("resource_names") or []),
            }

            lines = [
                "",
                "SECTION: API Orchestrator",
                f"  - Page size: {stats['page_size']}",
                f"  - Resource scope count: {stats['resource_scope']}",
            ]

            new_analysis = (state.get("analysis") or "")

            updated = state.copy()
            updated.update({
                "current_step": "api_orchestrator_prepared",
                "analysis": (new_analysis + "\n" + "\n".join(lines)).strip(),
                "api_orchestrator_stats": stats,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"APIOrchestratorNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "api_orchestrator_error",
                "error": f"API orchestration prep failed: {exc}",
            })
            return updated
