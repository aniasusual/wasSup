"""
Clarification Engine Node (Phase 8 - F)

Determines whether user input requires additional clarification and
selects the appropriate clarification strategy (contextual or
architecture-specific).
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class ClarificationEngineNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ClarificationEngineNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            question = state.get("question", "")
            extracted = state.get("extracted_entities") or {}
            missing = list(state.get("missing_info") or [])
            prior_questions = list(state.get("clarifying_questions") or [])

            needs_clarification = self._decide_needs_clarification(question, extracted, missing)
            strategy = self._select_strategy(extracted, missing)
            context = {
                "strategy": strategy,
                "detected_missing": missing,
                "prior_questions": len(prior_questions),
            }

            analysis_lines = [
                "",
                "NODE F | Clarification Engine",
                "  ------------------------------",
                f"  - Needs clarification: {'YES' if needs_clarification else 'NO'}",
                f"  - Strategy selected: {strategy.upper() if strategy else 'NONE'}",
                f"  - Missing fields detected: {len(missing)}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "clarification_engine_evaluated",
                "analysis": new_analysis,
                "needs_clarification": needs_clarification,
                "clarification_context": {
                    **context,
                    "evaluated_at": datetime.utcnow().isoformat(),
                },
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"ClarificationEngineNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "clarification_engine_error",
                "error": f"Clarification engine failed: {exc}",
            })
            return updated

    def _decide_needs_clarification(
        self,
        question: str,
        extracted: Dict[str, Any],
        missing: List[str],
    ) -> bool:
        if not question.strip():
            return True
        if missing:
            return True
        intent_indicators = extracted.get("intent_indicators") or []
        if intent_indicators and "ambiguous" in [i.lower() for i in intent_indicators]:
            return True
        services = extracted.get("services") or {}
        if len(services) == 0:
            return True
        return False

    def _select_strategy(self, extracted: Dict[str, Any], missing: List[str]) -> str:
        arch_needed = any(item in missing for item in ["service_specification", "architecture_scope"])
        services = extracted.get("services") or {}
        if arch_needed or len(services) > 3:
            return "architecture"
        if missing:
            return "contextual"
        return "none"

