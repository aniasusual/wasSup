"""
Intent & Query Analysis Node - Phases B and C combined.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ..llm_service import LLMService
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.agent.core.llm_service import LLMService


logger = logging.getLogger(__name__)


class IntentAndQueryAnalysisNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.IntentAndQueryAnalysisNode")
        self.llm_service = LLMService()

    async def execute(self, state: AgentState) -> AgentState:
        start_time = datetime.utcnow()
        try:
            question = state.get("question", "")
            if not question:
                return self._update_state_with_error(state, "Question missing in state")

            extracted_entities = await self.llm_service.extract_entities(question)
            formatted_entities = {
                "services": {f"resource.type={service}": True for service in extracted_entities.get("services", [])},
                "severities": extracted_entities.get("severities", []),
                "time_indicators": extracted_entities.get("time_indicators", []),
                "keywords": extracted_entities.get("keywords", []),
                "error_patterns": extracted_entities.get("error_patterns", []),
                "http_status_codes": extracted_entities.get("http_status_codes", []),
                "resource_identifiers": extracted_entities.get("resource_identifiers", []),
                "intent_indicators": extracted_entities.get("intent_indicators", [])
            }

            classification_result = await self.llm_service.classify_query(question, formatted_entities)
            query_type = classification_result.get("query_type", "simple")

            missing_info_result = await self.llm_service.detect_missing_information(question, formatted_entities, state)
            missing_info = missing_info_result.get("missing_information", [])

            needs_clarification = self._should_request_clarification(
                missing_info, query_type, classification_result
            )

            clarifying_questions = []
            if needs_clarification and classification_result:
                clarifying_questions = classification_result.get("clarification_questions", [])

            analysis = self._generate_analysis(state, formatted_entities, classification_result, needs_clarification)

            updated_state = state.copy()
            updated_state.update({
                "current_step": "intent_and_query_analysis_complete",
                "query_type": query_type,
                "extracted_entities": formatted_entities,
                "missing_info": missing_info,
                "needs_clarification": needs_clarification,
                "clarifying_questions": [{"question": q, "context": "nlp_generated"} for q in clarifying_questions],
                "analysis": analysis or state.get("analysis", ""),
                "tool_results": {
                    **(state.get("tool_results") or {}),
                    "nlp_analysis": {
                        "classification_result": classification_result,
                        "missing_info_analysis": missing_info_result
                    }
                }
            })

            exec_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(f"Intent and query analysis completed in {exec_time:.3f}s")
            return updated_state
        except Exception as e:
            self.logger.error(f"Error in IntentAndQueryAnalysisNode: {str(e)}", exc_info=True)
            return self._update_state_with_error(state, str(e))

    def _should_request_clarification(self, missing_info: List[str], query_type: str, classification_result: Optional[Dict[str, Any]] = None) -> bool:
        if classification_result:
            if classification_result.get("needs_clarification", False):
                return True
            llm_missing_info = classification_result.get("missing_information", [])
            if any(info in llm_missing_info for info in ["service_specification", "project_id"]):
                return True
            if classification_result.get("confidence", 1.0) < 0.5:
                return True
        if query_type == "ambiguous":
            return True
        if any(info in missing_info for info in ["service_specification", "project_id"]):
            return True
        if query_type == "complex" and len(missing_info) >= 2:
            return True
        return False

    def _generate_analysis(self, state: AgentState, extracted_entities: Dict[str, Any], classification_result: Dict[str, Any], needs_clarification: bool) -> str:
        question = state.get("question", "")
        project_id = state.get("project_id", "")
        parts: List[str] = []
        parts.append(f"## 🔍 **Query Analysis**")
        parts.append(f"**Original Query:** {question}")
        parts.append(f"**Project ID:** {project_id}")
        if extracted_entities.get("services"):
            services = list(extracted_entities["services"].keys())
            parts.append(f"**Target Services:** {', '.join(services)}")
        if extracted_entities.get("severities"):
            parts.append(f"**Severity Levels:** {', '.join(extracted_entities['severities'])}")
        if extracted_entities.get("time_indicators"):
            parts.append(f"**Time Range:** {', '.join(extracted_entities['time_indicators'])}")
        qtype = classification_result.get("query_type", "unknown")
        confidence = classification_result.get("confidence", 0.0)
        reasoning = classification_result.get("reasoning", "")
        parts.append(f"\n## 🧠 **Intelligence Analysis**")
        parts.append(f"**Query Type:** {qtype.title()}")
        parts.append(f"**Confidence:** {confidence:.1%}")
        parts.append(f"**Reasoning:** {reasoning}")
        if needs_clarification:
            parts.append(f"\n## ❓ **Clarification Needed**")
            parts.append("I need some additional information to provide the most accurate results:")
            for question in classification_result.get("clarification_questions", []):
                parts.append(f"• {question}")
        else:
            parts.append(f"\n## ✅ **Ready to Proceed**")
            parts.append("I have enough information to start the investigation. I'll now:")
            parts.append("1. **Fetch logs** from the specified GCP services")
            parts.append("2. **Filter by severity** and time range")
            parts.append("3. **Analyze patterns** and provide insights")
            parts.append("4. **Suggest actions** based on findings")
        suggested_scope = classification_result.get("suggested_scope", "")
        if suggested_scope:
            parts.append(f"\n## 🎯 **Suggested Investigation Scope**")
            parts.append(suggested_scope)
        return "\n".join(parts)

    def _update_state_with_error(self, state: AgentState, error_message: str) -> AgentState:
        updated_state = state.copy()
        updated_state.update({
            "current_step": "intent_and_query_analysis_error",
            "error": error_message,
            "needs_clarification": True,
            "clarifying_questions": [{
                "question": "There was an issue analyzing your query. Please try rephrasing it.",
                "context": "nlp_processing_error"
            }]
        })
        return updated_state

