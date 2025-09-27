"""
Cross-Project Learning Node (Phase 13 - FFFF)

Aggregates insights across projects for transfer learning.
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


class CrossProjectLearningNode:
    """Record cross-project learning metrics."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CrossProjectLearningNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            learning_meta = state.get("architecture_learning_meta") or {}
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "entries": learning_meta.get("total_entries"),
                "top_services": (learning_meta.get("top_services") or [])[:3],
            }

            lines = [
                "",
                "SECTION: Cross-Project Learning",
                f"  - Learning entries: {summary['entries'] if summary['entries'] is not None else 'n/a'}",
            ]
            if summary["top_services"]:
                lines.append(f"  - Focus services: {', '.join(summary['top_services'])}")

            updated = state.copy()
            updated.update({
                "current_step": "cross_project_learning_complete",
                "analysis": ((state.get("analysis") or "") + "\n" + "\n".join(lines)).strip(),
                "cross_project_learning_summary": summary,
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"CrossProjectLearningNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "cross_project_learning_error",
                "error": f"Cross-project learning failed: {exc}",
            })
            return updated
