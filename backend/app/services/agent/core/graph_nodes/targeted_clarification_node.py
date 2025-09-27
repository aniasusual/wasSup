"""
Targeted Clarification Node (Phase 7 - CC)

Creates focused clarification prompts when confidence is medium,
ensuring the system requests only the critical missing context.
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


class TargetedClarificationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.TargetedClarificationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            missing = state.get("missing_info") or []
            generated = self._generate_questions(bundle, missing)

            analysis_lines = [
                "",
                "NODE CC | Targeted Clarification",
                "  --------------------------------",
                f"  - Clarification prompts generated: {len(generated)}",
            ]
            for idx, prompt in enumerate(generated[:3], start=1):
                analysis_lines.append(f"  - Prompt {idx}: {prompt}")

            updated_questions = list(state.get("clarifying_questions") or [])
            for prompt in generated:
                updated_questions.append({
                    "question": prompt,
                    "context": "targeted_confidence_gap",
                    "created_at": datetime.utcnow().isoformat(),
                })

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "targeted_clarification_requested",
                "analysis": new_analysis,
                "needs_clarification": True,
                "clarifying_questions": updated_questions,
                "clarification_context": {
                    "reason": "medium_confidence",
                    "requested_at": datetime.utcnow().isoformat(),
                },
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"TargetedClarificationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "targeted_clarification_error",
                "error": f"Targeted clarification failed: {exc}",
            })
            return updated

    def _generate_questions(self, bundle: Dict[str, Any], missing: List[str]) -> List[str]:
        prompts: List[str] = []
        if missing:
            for item in missing[:3]:
                prompts.append(f"Could you provide details for: {item}?")

        services = bundle.get("services_in_focus") or []
        related_paths = bundle.get("related_paths") or []
        if services and not prompts:
            prompts.append(f"Confirm if the issue reproducible on {services[0]} at current timeframe?")
        if related_paths:
            prompts.append("Do you observe anomalies along the highlighted dependency chain?")

        if not prompts:
            prompts.append("Please share any additional symptoms or affected components relevant to this incident.")
        return prompts

