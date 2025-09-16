"""
LangGraph workflow nodes implementation.

This module contains all the individual nodes that make up the
agent workflow graph.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    # Try relative imports first (for normal usage)
    from ....models.agent import AgentState, NodeResult, WorkflowConfig, QueryInput
    from .llm_service import LLMService
except ImportError:
    # Fall back to absolute imports (for LangGraph Studio)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from app.models.agent import AgentState, NodeResult, WorkflowConfig, QueryInput
    from app.services.agent.core.llm_service import LLMService

logger = logging.getLogger(__name__)


class UserQueryInputNode:
    """
    User Query Input Node - Phase 1, Step 1 of the investigation workflow.
    
    This node handles the initial processing of user queries including:
    - Input validation and sanitization
    - Basic preprocessing and normalization
    - Initial entity extraction
    - Query type classification (simple/complex/ambiguous)
    - Missing information detection
    """
    
    def __init__(self, config: WorkflowConfig):
        """
        Initialize the User Query Input node.
        
        Args:
            config: Workflow configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.UserQueryInputNode")
        
        # Initialize LLM service for NLP-based entity extraction and classification
        self.llm_service = LLMService()
        
        self.logger.info("UserQueryInputNode initialized with LLM service")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the User Query Input node.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with processed query information
        """
        start_time = datetime.utcnow()
        
        try:
            
            self.logger.info(f"Processing user query: {state.get('question', '')[:100]}...")
            
            # Validate and process the input
            validation_result = self._validate_input(state)
            if not validation_result.success:
                return self._update_state_with_error(state, validation_result.error)
            
            
            # Extract entities using LLM
            extracted_entities = await self._extract_entities_nlp(state["question"])
            
            # Classify query type using LLM
            classification_result = await self._classify_query_nlp(state["question"], extracted_entities)
            query_type = classification_result.get("query_type", "simple")
            
            # Detect missing information using NLP
            missing_info_result = await self._detect_missing_info_nlp(state, extracted_entities)
            missing_info = missing_info_result.get("missing_information", [])
            
            # Determine if clarification is needed (use LLM classification if available)
            needs_clarification = self._should_request_clarification(
                missing_info, 
                query_type, 
                classification_result
            )
            
            # Generate clarification questions if needed
            clarifying_questions = []
            if needs_clarification and classification_result:
                clarifying_questions = classification_result.get("clarification_questions", [])
            
            # Generate analysis based on extracted entities and classification
            analysis = self._generate_analysis(state, extracted_entities, classification_result, needs_clarification)
            
            # Update state with processed information
            updated_state = state.copy()
            updated_state.update({
                "current_step": "user_query_input_complete",
                "query_type": query_type,
                "extracted_entities": extracted_entities,
                "processed_question": self._preprocess_question(state["question"]),
                "missing_info": missing_info,
                "needs_clarification": needs_clarification,
                "clarifying_questions": [{"question": q, "context": "nlp_generated"} for q in clarifying_questions],
                "analysis": analysis,
                "tool_results": {
                    "user_parameters": {
                        "search_query": state["question"],
                        "resource_filters": extracted_entities.get("services", {}),
                        "severity_filters": extracted_entities.get("severities", []),
                        "time_range": state.get("time_range")
                    },
                    "nlp_analysis": {
                        "classification_result": classification_result,
                        "missing_info_analysis": missing_info_result
                    }
                }
            })
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"User query processing completed in {execution_time:.3f}s")
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in UserQueryInputNode: {str(e)}", exc_info=True)
            return self._update_state_with_error(state, str(e))
    
    def _validate_input(self, state: AgentState) -> NodeResult:
        """
        Validate the user input for required fields and format.
        
        Args:
            state: Current agent state
            
        Returns:
            NodeResult indicating validation success/failure
        """
        
        try:
            # Check required fields
            if not state.get("question", "").strip():
                return NodeResult(
                    success=False,
                    error="Question is required and cannot be empty"
                )
            
            if not state.get("project_id", "").strip():
                return NodeResult(
                    success=False,
                    error="Project ID is required"
                )
            
            # Validate question length
            question = state["question"].strip()
            if len(question) < 3:
                return NodeResult(
                    success=False,
                    error="Question must be at least 3 characters long"
                )
            
            if len(question) > 2000:
                return NodeResult(
                    success=False,
                    error="Question must be less than 2000 characters"
                )
            
            # Validate project ID format (basic GCP project ID validation)
            project_id = state["project_id"]
            # GCP project IDs: 6-30 characters, lowercase letters, numbers, hyphens
            # Must start with a letter, can end with letter or number
            if (not project_id or 
                len(project_id) < 6 or 
                len(project_id) > 30 or
                not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', project_id)):
                return NodeResult(
                    success=False,
                    error="Invalid GCP project ID format"
                )
            
            return NodeResult(
                success=True,
                message="Input validation successful",
                execution_time=0.001
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
    
    async def _extract_entities_nlp(self, question: str) -> Dict[str, Any]:
        """
        Extract entities from user question using NLP (LLM).
        
        Args:
            question: User question text
            
        Returns:
            Dictionary of extracted entities
        """
        # Use LLM service for entity extraction
        entities = await self.llm_service.extract_entities(question)
        
        # Convert LLM output to expected format
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
        """
        Classify query type using NLP (LLM).
        
        Args:
            question: User question text
            entities: Extracted entities
            
        Returns:
            Dictionary containing classification results
        """
        # Use LLM service for query classification
        classification = await self.llm_service.classify_query(question, entities)
        return classification
    
    async def _detect_missing_info_nlp(self, state: AgentState, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect missing information using NLP (LLM).
        
        Args:
            state: Current agent state
            entities: Extracted entities
            
        Returns:
            Dictionary containing missing information analysis
        """
        # Use LLM service for intelligent missing information detection
        missing_info_result = await self.llm_service.detect_missing_information(
            state["question"], 
            entities, 
            state
        )
        return missing_info_result
    
    def _should_request_clarification(self, missing_info: List[str], query_type: str, classification_result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if clarification is needed based on missing information and query type.
        
        Args:
            missing_info: List of missing information
            query_type: Classified query type
            classification_result: Optional LLM classification results
            
        Returns:
            True if clarification should be requested
        """
        # Use LLM classification results if available
        if classification_result:
            # Check if LLM explicitly determined clarification is needed
            if classification_result.get("needs_clarification", False):
                return True
            
            llm_missing_info = classification_result.get("missing_information", [])
            # Only request clarification if critical information is missing
            critical_missing = ["service_specification", "project_id"]
            if any(info in llm_missing_info for info in critical_missing):
                return True
            
            # Check confidence level - be more lenient
            confidence = classification_result.get("confidence", 1.0)
            if confidence < 0.5:  # Lowered threshold
                return True
        
        # Always request clarification for ambiguous queries
        if query_type == "ambiguous":
            return True
        
        # Request clarification if critical information is missing
        critical_missing = ["service_specification", "project_id"]
        if any(info in missing_info for info in critical_missing):
            return True
        
        # Request clarification for complex queries with missing context
        if query_type == "complex" and len(missing_info) >= 2:
            return True
        
        return False
    
    def _preprocess_question(self, question: str) -> str:
        """
        Preprocess and normalize the question text.
        
        Args:
            question: Original question text
            
        Returns:
            Preprocessed question text
        """
        # Basic normalization
        processed = question.strip()
        
        # Expand common abbreviations
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
        """
        Update state with error information.
        
        Args:
            state: Current agent state
            error_message: Error message to include
            
        Returns:
            Updated state with error information
        """
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
    
    def _generate_analysis(self, state: AgentState, extracted_entities: Dict[str, Any], classification_result: Dict[str, Any], needs_clarification: bool) -> str:
        """
        Generate analysis based on extracted entities and classification.
        
        Args:
            state: Current agent state
            extracted_entities: Extracted entities from the query
            classification_result: Query classification results
            needs_clarification: Whether clarification is needed
            
        Returns:
            Generated analysis text
        """
        question = state.get("question", "")
        project_id = state.get("project_id", "")
        
        # Build analysis based on extracted information
        analysis_parts = []
        
        # Query understanding
        analysis_parts.append(f"## 🔍 **Query Analysis**")
        analysis_parts.append(f"**Original Query:** {question}")
        analysis_parts.append(f"**Project ID:** {project_id}")
        
        # Extracted entities
        if extracted_entities.get("services"):
            services = list(extracted_entities["services"].keys())
            analysis_parts.append(f"**Target Services:** {', '.join(services)}")
        
        if extracted_entities.get("severities"):
            severities = extracted_entities["severities"]
            analysis_parts.append(f"**Severity Levels:** {', '.join(severities)}")
        
        if extracted_entities.get("time_indicators"):
            time_indicators = extracted_entities["time_indicators"]
            analysis_parts.append(f"**Time Range:** {', '.join(time_indicators)}")
        
        # Classification insights
        query_type = classification_result.get("query_type", "unknown")
        confidence = classification_result.get("confidence", 0.0)
        reasoning = classification_result.get("reasoning", "")
        
        analysis_parts.append(f"\n## 🧠 **Intelligence Analysis**")
        analysis_parts.append(f"**Query Type:** {query_type.title()}")
        analysis_parts.append(f"**Confidence:** {confidence:.1%}")
        analysis_parts.append(f"**Reasoning:** {reasoning}")
        
        # Next steps
        if needs_clarification:
            analysis_parts.append(f"\n## ❓ **Clarification Needed**")
            analysis_parts.append("I need some additional information to provide the most accurate results:")
            for question in classification_result.get("clarification_questions", []):
                analysis_parts.append(f"• {question}")
        else:
            analysis_parts.append(f"\n## ✅ **Ready to Proceed**")
            analysis_parts.append("I have enough information to start the investigation. I'll now:")
            analysis_parts.append("1. **Fetch logs** from the specified GCP services")
            analysis_parts.append("2. **Filter by severity** and time range")
            analysis_parts.append("3. **Analyze patterns** and provide insights")
            analysis_parts.append("4. **Suggest actions** based on findings")
        
        # Suggested scope
        suggested_scope = classification_result.get("suggested_scope", "")
        if suggested_scope:
            analysis_parts.append(f"\n## 🎯 **Suggested Investigation Scope**")
            analysis_parts.append(suggested_scope)
        
        return "\n".join(analysis_parts)
