"""
Pattern Analyzer Node (Phase 12 - TTT)

Derives pattern summaries from the multi-dimensional analysis outputs.
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


class PatternAnalyzerNode:
    """Summarise log patterns for correlation workflows."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PatternAnalyzerNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            md_summary = state.get("md_summary") or {}
            top_messages = md_summary.get("top_messages") or []

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "top_message": top_messages[0]["message"] if top_messages else None,
                "error_rate": md_summary.get("error_rate"),
            }

            lines = [
                "",
                "SECTION: Pattern Analyzer",
                f"  - Error rate: {summary['error_rate'] if summary['error_rate'] is not None else 'n/a'}",
            ]
            if summary["top_message"]:
                lines.append(f"  - Top message: {summary['top_message']}")

            new_analysis = (state.get("analysis") or "")
            updated = state.copy()
            updated.update({
                "current_step": "pattern_analyzer_complete",
                "analysis": (new_analysis + "\n" + "\n".join(lines)).strip(),
                "pattern_analyzer_summary": summary,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"PatternAnalyzerNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "pattern_analyzer_error",
                "error": f"Pattern analyzer failed: {exc}",
            })
            return updated
