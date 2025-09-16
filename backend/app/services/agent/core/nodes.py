"""
Deprecated shim: node classes were moved into the graph_nodes package.
This module re-exports them for backward compatibility.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .graph_nodes.user_query_input_node import UserQueryInputNode
from .graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
from .llm_service import LLMService
from ....models.agent import AgentState, WorkflowConfig

__all__ = [
    "UserQueryInputNode",
    "IntentAndQueryAnalysisNode",
]


class IntentAndQueryAnalysisNode:
    """
    Combined Intent Classification (B) & Query Type Analysis (C) node.
    Runs after architecture context is loaded so NLP can use that context later.
    Minimal duplication of logic from UserQueryInputNode to avoid broad refactors.
    """

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

            # Extract entities using LLM
            extracted_entities = await self._extract_entities_nlp(question)

            # Classify query type using LLM
            classification_result = await self._classify_query_nlp(question, extracted_entities)
            query_type = classification_result.get("query_type", "simple")

            # Detect missing information using NLP
            missing_info_result = await self._detect_missing_info_nlp(state, extracted_entities)
            missing_info = missing_info_result.get("missing_information", [])

            # Determine if clarification is needed
            needs_clarification = self._should_request_clarification(
                missing_info, query_type, classification_result
            )

            clarifying_questions = []
            if needs_clarification and classification_result:
                clarifying_questions = classification_result.get("clarification_questions", [])

            analysis = self._generate_analysis(state, extracted_entities, classification_result, needs_clarification)

            updated_state = state.copy()
            updated_state.update({
                "current_step": "intent_and_query_analysis_complete",
                "query_type": query_type,
                "extracted_entities": extracted_entities,
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

    # Reuse the helper methods logic from UserQueryInputNode (duplicated minimally)
    async def _extract_entities_nlp(self, question: str) -> Dict[str, Any]:
        entities = await self.llm_service.extract_entities(question)
        formatted_entities = {
            "services": {f"resource.type={service}": True for service in entities.get("services", [])},
            "severities": entities.get("severities", []),
            "time_indicators": entities.get("time_indicators", []),
            "keywords": entities.get("keywords", []),
            "error_patterns": entities.get("error_patterns", []),
            "http_status_codes": entities.get("http_status_codes", []),
            "resource_identifiers": entities.get("resource_identifiers", []),
            "intent_indicators": entities.get("intent_indicators", [])
        }
        return formatted_entities

    async def _classify_query_nlp(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        return await self.llm_service.classify_query(question, entities)

    async def _detect_missing_info_nlp(self, state: AgentState, entities: Dict[str, Any]) -> Dict[str, Any]:
        return await self.llm_service.detect_missing_information(state.get("question", ""), entities, state)

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
        # Mirror formatting from UserQueryInputNode
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
