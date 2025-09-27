"""
Context Manager Node (Phase 12 - WWW)

Consolidates final context state before queuing history updates.
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


class ContextManagerNode:
    """Summarise context snapshot for agent persistence."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ContextManagerNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            timestamp = datetime.utcnow().isoformat()
            snapshot = {
                "timestamp": timestamp,
                "context_memory_entries": len((state.get("context_memory") or {}).get("entries") or []),
                "query_history_entries": len(state.get("query_history") or []),
                "preventive_actions": len(state.get("preventive_actions") or []),
            }

            lines = [
                "",
                "SECTION: Context Manager",
                f"  - Memory entries: {snapshot['context_memory_entries']}",
                f"  - History entries: {snapshot['query_history_entries']}",
            ]

            new_analysis = (state.get("analysis") or "")
            updated = state.copy()
            updated.update({
                "current_step": "context_manager_complete",
                "analysis": (new_analysis + "\n" + "\n".join(lines)).strip(),
                "context_manager_snapshot": snapshot,
            })

            if self.config.enable_learning and state.get("project_id"):
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        state.get("project_id"),
                        {"context_manager_snapshot": snapshot},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Context manager persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ContextManagerNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "context_manager_error",
                "error": f"Context manager failed: {exc}",
            })
            return updated
