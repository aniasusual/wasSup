"""
User Query Input Node - Phase 1, Step A of the investigation workflow.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .....models.agent import AgentState, NodeResult, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, NodeResult, WorkflowConfig


logger = logging.getLogger(__name__)


class UserQueryInputNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.UserQueryInputNode")
        self.logger.info("UserQueryInputNode initialized")

    async def execute(self, state: AgentState) -> AgentState:
        start_time = datetime.utcnow()
        try:
            self.logger.info(f"Processing user query (input stage): {state.get('question', '')[:100]}...")
            validation_result = self._validate_input(state)
            if not validation_result.success:
                return self._update_state_with_error(state, validation_result.error)

            processed_question = self._preprocess_question(state["question"]) 

            updated_state = state.copy()
            updated_state.update({
                "current_step": "user_query_input_complete",
                "processed_question": processed_question,
                "query_type": None,
                "extracted_entities": {},
                "missing_info": [],
                "needs_clarification": False,
                "clarifying_questions": [],
                "analysis": state.get("analysis") or "",
                "tool_results": {
                    **(state.get("tool_results") or {}),
                    "user_parameters": {
                        "search_query": state["question"],
                        "time_range": state.get("time_range")
                    }
                }
            })

            exec_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(f"User input processed in {exec_time:.3f}s")
            return updated_state
        except Exception as e:
            self.logger.error(f"Error in UserQueryInputNode: {str(e)}", exc_info=True)
            return self._update_state_with_error(state, str(e))

    def _validate_input(self, state: AgentState) -> NodeResult:
        try:
            if not state.get("question", "").strip():
                return NodeResult(success=False, error="Question is required and cannot be empty")
            if not state.get("project_id", "").strip():
                return NodeResult(success=False, error="Project ID is required")
            question = state["question"].strip()
            if len(question) < 3:
                return NodeResult(success=False, error="Question must be at least 3 characters long")
            if len(question) > 2000:
                return NodeResult(success=False, error="Question must be less than 2000 characters")
            project_id = state["project_id"]
            if (
                not project_id or len(project_id) < 6 or len(project_id) > 30 or
                not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', project_id)
            ):
                return NodeResult(success=False, error="Invalid GCP project ID format")
            return NodeResult(success=True, message="Input validation successful", execution_time=0.001)
        except Exception as e:
            return NodeResult(success=False, error=f"Validation error: {str(e)}")

    def _preprocess_question(self, question: str) -> str:
        processed = question.strip()
        abbreviations = {
            'gcp': 'Google Cloud Platform',
            'gce': 'Google Compute Engine',
            'gke': 'Google Kubernetes Engine',
            'sql': 'SQL database',
            'api': 'API',
            'http': 'HTTP',
            'https': 'HTTPS'
        }
        for abbr, expansion in abbreviations.items():
            processed = re.sub(rf'\b{abbr}\b', expansion, processed, flags=re.IGNORECASE)
        return processed

    def _update_state_with_error(self, state: AgentState, error_message: str) -> AgentState:
        updated_state = state.copy()
        updated_state.update({
            "current_step": "user_query_input_error",
            "error": error_message,
            "needs_clarification": True,
            "clarifying_questions": [{
                "question": "There was an issue processing your query. Please check your input and try again.",
                "context": "input_validation_error"
            }]
        })
        return updated_state

