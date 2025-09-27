"""
Contextual Question Generator Node (Phase 8 - G)

Produces clarification questions tailored to the user's query and the
project architecture context.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

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


class ContextualQuestionGeneratorNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ContextualQuestionGeneratorNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            clar_context = state.get("clarification_context") or {}
            missing = list(state.get("missing_info") or [])
            extracted = state.get("extracted_entities") or {}

            architecture_questions = []
            if project_id:
                architecture_questions = await self._architecture_based_questions(project_id, extracted)

            contextual_questions = self._context_questions(extracted, missing)
            combined = architecture_questions + contextual_questions

            analysis_lines = [
                "",
                "NODE G | Contextual Questions",
                "  -----------------------------",
                f"  - Questions generated: {len(combined)}",
            ]
            for idx, question in enumerate(combined[:4], start=1):
                analysis_lines.append(f"  - Question {idx}: {question}")

            updated_questions = list(state.get("clarifying_questions") or [])
            timestamp = datetime.utcnow().isoformat()
            for question in combined:
                updated_questions.append({
                    "question": question,
                    "context": "contextual_clarification",
                    "created_at": timestamp,
                })

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "contextual_questions_generated",
                "analysis": new_analysis,
                "clarifying_questions": updated_questions,
                "clarification_context": {
                    **clar_context,
                    "last_question_generated_at": timestamp,
                },
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"ContextualQuestionGeneratorNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "contextual_question_generation_error",
                "error": f"Contextual question generation failed: {exc}",
            })
            return updated

    async def _architecture_based_questions(
        self,
        project_id: str,
        extracted: Dict[str, Any],
    ) -> List[str]:
        questions: List[str] = []
        try:
            topology = await project_architecture_service.get_topology_map(project_id)
            services = topology.get("services") or []
            if services:
                service_names = [svc.get("name") for svc in services if svc.get("name")]
                if service_names and not extracted.get("services"):
                    subset = ", ".join(service_names[:3])
                    questions.append(f"Which service should we focus on? Options include: {subset}")
        except Exception as fetch_err:
            self.logger.debug(f"Topology fetch failed during clarification: {fetch_err}")
        return questions

    def _context_questions(self, extracted: Dict[str, Any], missing: List[str]) -> List[str]:
        questions: List[str] = []
        if "time_range" in missing:
            questions.append("What time range should we analyze (e.g., last hour, last 24h)?")
        if "issue_type" in missing:
            questions.append("What type of issue are you seeing (errors, latency, availability)?")
        keywords = extracted.get("keywords") or []
        if keywords:
            questions.append("Do you want to focus on the keywords already detected, or broaden the search?")
        if not questions:
            questions.append("Provide any extra context that would help narrow the investigation.")
        return questions

