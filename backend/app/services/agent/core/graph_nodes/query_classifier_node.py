"""
Query Classifier Node (Phase 12 - OOO)

Refines query classification metadata for downstream planning.
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


class QueryClassifierNode:
    """Augment query classification details for agent orchestration."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.QueryClassifierNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "query_type": state.get("query_type"),
                "needs_clarification": state.get("needs_clarification", False),
                "missing_info": list(state.get("missing_info") or [])[:5],
            }

            lines = [
                "",
                "SECTION: Query Classifier",
                f"  - Type: {summary['query_type'] or 'unknown'}",
                f"  - Needs clarification: {summary['needs_clarification']}",
            ]
            if summary["missing_info"]:
                lines.append(f"  - Missing info: {', '.join(summary['missing_info'])}")

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "query_classified",
                "analysis": new_analysis,
                "query_classifier_summary": summary,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"QueryClassifierNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "query_classifier_error",
                "error": f"Query classifier failed: {exc}",
            })
            return updated
