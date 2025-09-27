"""
Architecture-Specific Question Node (Phase 8 - FF)

Uses project architecture data to ask precise clarification questions
about services, dependencies, or resources.
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


class ArchitectureSpecificQuestionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchitectureSpecificQuestionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                return state

            clarification_context = state.get("clarification_context") or {}
            prior_questions = list(state.get("clarifying_questions") or [])

            questions = await self._build_arch_questions(project_id, clarification_context)
            analysis_lines = [
                "",
                "NODE FF | Architecture-Specific Questions",
                "  -----------------------------------------",
                f"  - Architecture questions generated: {len(questions)}",
            ]
            for idx, question in enumerate(questions[:3], start=1):
                analysis_lines.append(f"  - Question {idx}: {question}")

            timestamp = datetime.utcnow().isoformat()
            for question in questions:
                prior_questions.append({
                    "question": question,
                    "context": "architecture_clarification",
                    "created_at": timestamp,
                })

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "architecture_questions_generated",
                "analysis": new_analysis,
                "clarifying_questions": prior_questions,
                "clarification_context": {
                    **clarification_context,
                    "architecture_questions_generated_at": timestamp,
                },
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"ArchitectureSpecificQuestionNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "architecture_question_generation_error",
                "error": f"Architecture-specific clarification failed: {exc}",
            })
            return updated

    async def _build_arch_questions(
        self,
        project_id: str,
        clar_context: Dict[str, Any],
    ) -> List[str]:
        questions: List[str] = []
        try:
            registry = await project_architecture_service.get_service_registry(project_id)
            if registry:
                names = [svc.get("name") for svc in registry if svc.get("name")]
                if names:
                    subset = ", ".join(names[:3])
                    questions.append(f"Narrow to services impacting {subset}?")

            flows = await project_architecture_service.get_data_flow_patterns(project_id)
            if flows:
                flow = flows[0]
                hops = flow.get("hops")
                if hops:
                    questions.append(
                        "Should we include dependent services along the path: "
                        + " -> ".join(hops[:4])
                    )
        except Exception as fetch_err:
            self.logger.debug(f"Failed to build architecture questions: {fetch_err}")
        return questions

