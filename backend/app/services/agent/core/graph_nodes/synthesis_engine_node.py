"""
Synthesis Engine Node (Phase 12 - UUU)

Creates synthesis insights from the root cause summary.
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


class SynthesisEngineNode:
    """Summarise synthesis outputs for LangGraph agent integration."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SynthesisEngineNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            root_cause = state.get("root_cause_summary") or {}
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "primary_cause": root_cause.get("primary_cause"),
                "confidence": root_cause.get("confidence"),
            }

            lines = [
                "",
                "SECTION: Synthesis Engine",
                f"  - Primary cause: {summary['primary_cause'] or 'n/a'}",
                f"  - Confidence: {summary['confidence'] or 'n/a'}",
            ]

            new_analysis = (state.get("analysis") or "")
            updated = state.copy()
            updated.update({
                "current_step": "synthesis_engine_complete",
                "analysis": (new_analysis + "\n" + "\n".join(lines)).strip(),
                "synthesis_summary": summary,
            })

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"SynthesisEngineNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "synthesis_engine_error",
                "error": f"Synthesis engine failed: {exc}",
            })
            return updated
