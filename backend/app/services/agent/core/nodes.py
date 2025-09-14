"""
LangGraph workflow nodes implementation.

This module contains all the individual nodes that make up the
agent workflow graph.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from ....models.agent import AgentState, NodeResult, WorkflowConfig, QueryInput
from .llm_service import LLMService

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
        
        # Keep fallback patterns for when LLM is not available
        self.service_patterns = {
            'cloud_run': r'\b(?:cloud.?run|cloudrun|run)\b',
            'cloud_sql': r'\b(?:cloud.?sql|cloudsql|sql)\b',
            'gce_instance': r'\b(?:gce|compute.?engine|compute.?instance|vm|instance)\b',
            'gke_cluster': r'\b(?:gke|kubernetes|k8s|cluster)\b',
            'app_engine': r'\b(?:app.?engine|gae)\b',
            'cloud_functions': r'\b(?:cloud.?functions|functions|gcf)\b',
            'load_balancer': r'\b(?:load.?balancer|lb|ingress)\b',
            'cloud_storage': r'\b(?:cloud.?storage|storage|gcs|bucket)\b'
        }
        
        # Severity patterns
        self.severity_patterns = {
            'error': r'\b(?:error|err|failed|failure|exception|critical|fatal)\b',
            'warning': r'\b(?:warning|warn|caution|alert)\b',
            'info': r'\b(?:info|information|debug|trace)\b'
        }
        
        # Time range patterns
        self.time_patterns = {
            'last_hour': r'\b(?:last.?hour|past.?hour|hour)\b',
            'last_day': r'\b(?:last.?day|past.?day|day|yesterday)\b',
            'last_week': r'\b(?:last.?week|past.?week|week)\b',
            'recent': r'\b(?:recent|recently|lately)\b'
        }
        
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
            
            # Extract entities using LLM (with fallback to regex)
            extracted_entities = await self._extract_entities_nlp(state["question"])
            
            # Classify query type using LLM (with fallback to rule-based)
            classification_result = await self._classify_query_nlp(state["question"], extracted_entities)
            query_type = classification_result.get("query_type", "simple")
            
            # Detect missing information using NLP (with fallback)
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
            if not project_id or not re.match(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$', project_id):
                return NodeResult(
                    success=False,
                    error="Invalid GCP project ID format"
                )
            
            # Validate limit if provided
            limit = state.get("limit", 1000)
            if not isinstance(limit, int) or limit < 1 or limit > 10000:
                return NodeResult(
                    success=False,
                    error="Limit must be an integer between 1 and 10000"
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
        Extract entities from user question using NLP (LLM) with regex fallback.
        
        Args:
            question: User question text
            
        Returns:
            Dictionary of extracted entities
        """
        try:
            # Use LLM service for entity extraction
            entities = await self.llm_service.extract_entities(question)
            
            # Convert LLM output to expected format
            return {
                "services": {f"resource.type={service}": True for service in entities.get("services", [])},
                "severities": entities.get("severities", []),
                "time_indicators": entities.get("time_indicators", []),
                "keywords": entities.get("keywords", []),
                "error_patterns": entities.get("error_patterns", []),
                "http_status_codes": entities.get("http_status_codes", []),
                "resource_identifiers": entities.get("resource_identifiers", []),
                "intent_indicators": entities.get("intent_indicators", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error in NLP entity extraction: {str(e)}")
            # Fallback to regex-based extraction
            return self._extract_entities_regex(question)
    
    async def _classify_query_nlp(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify query type using NLP (LLM) with rule-based fallback.
        
        Args:
            question: User question text
            entities: Extracted entities
            
        Returns:
            Dictionary containing classification results
        """
        try:
            # Use LLM service for query classification
            classification = await self.llm_service.classify_query(question, entities)
            return classification
            
        except Exception as e:
            self.logger.error(f"Error in NLP query classification: {str(e)}")
            # Fallback to rule-based classification
            return self._classify_query_regex(question, entities)
    
    async def _detect_missing_info_nlp(self, state: AgentState, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect missing information using NLP (LLM) with regex fallback.
        
        Args:
            state: Current agent state
            entities: Extracted entities
            
        Returns:
            Dictionary containing missing information analysis
        """
        try:
            # Use LLM service for intelligent missing information detection
            missing_info_result = await self.llm_service.detect_missing_information(
                state["question"], 
                entities, 
                state
            )
            return missing_info_result
            
        except Exception as e:
            self.logger.error(f"Error in NLP missing info detection: {str(e)}")
            # Fallback to rule-based detection
            return self._detect_missing_info_regex(state, entities)
    
    def _extract_entities_regex(self, question: str) -> Dict[str, Any]:
        """
        Extract entities from the user question using pattern matching.
        
        Args:
            question: User question text
            
        Returns:
            Dictionary of extracted entities
        """
        question_lower = question.lower()
        entities = {
            "services": {},
            "severities": [],
            "time_indicators": [],
            "keywords": [],
            "numbers": [],
            "urls": [],
            "error_codes": []
        }
        
        # Extract GCP services using dynamic patterns
        for service_name, pattern in self.service_patterns.items():
            if re.search(pattern, question_lower):
                entities["services"][f"resource.type={service_name}"] = True
        
        # Additional intelligent service detection
        if re.search(r'\b(?:kubernetes|k8s|container)\b', question_lower):
            entities["services"]["resource.type=gke_cluster"] = True
        if re.search(r'\b(?:function|lambda|serverless)\b', question_lower):
            entities["services"]["resource.type=cloud_functions"] = True
        if re.search(r'\b(?:database|db|sql|mysql|postgres)\b', question_lower):
            entities["services"]["resource.type=cloud_sql"] = True
        
        # Extract severity levels with enhanced detection
        for severity, pattern in self.severity_patterns.items():
            if re.search(pattern, question_lower):
                entities["severities"].append(severity.upper())
        
        # Additional intelligent severity detection
        if re.search(r'\b(?:fail|failure|broken|down|crash)\b', question_lower):
            entities["severities"].append("ERROR")
        if re.search(r'\b(?:slow|latency|timeout|delay)\b', question_lower):
            entities["severities"].append("WARNING")
        if re.search(r'\b(?:info|information|status|health)\b', question_lower):
            entities["severities"].append("INFO")
        
        # Extract time indicators with enhanced detection
        for time_type, pattern in self.time_patterns.items():
            if re.search(pattern, question_lower):
                entities["time_indicators"].append(time_type)
        
        # Additional intelligent time detection
        if re.search(r'\b(?:today|now|current)\b', question_lower):
            entities["time_indicators"].append("today")
        if re.search(r'\b(?:yesterday|previous day)\b', question_lower):
            entities["time_indicators"].append("yesterday")
        if re.search(r'\b(?:this week|past week)\b', question_lower):
            entities["time_indicators"].append("this_week")
        if re.search(r'\b(?:since|from|starting)\b', question_lower):
            entities["time_indicators"].append("since_time")
        
        # Extract HTTP status codes
        status_codes = re.findall(r'\b(?:5\d{2}|4\d{2})\b', question)
        entities["error_codes"].extend(status_codes)
        
        # Extract numbers (could be time ranges, limits, etc.)
        numbers = re.findall(r'\b\d+\b', question)
        entities["numbers"].extend(numbers)
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', question)
        entities["urls"].extend(urls)
        
        # Extract general keywords with intelligent filtering
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'are', 'was', 'were', 'being', 'been', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'i'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question_lower)
        keywords = [word for word in words if word not in stop_words]
        
        # Prioritize technical and GCP-related keywords
        technical_terms = ['authentication', 'authorization', 'performance', 'latency', 'throughput', 'scalability', 'availability', 'reliability', 'monitoring', 'logging', 'debugging', 'troubleshooting', 'analysis', 'investigation', 'correlation', 'dependency', 'impact', 'failure', 'error', 'exception', 'timeout', 'connection', 'network', 'database', 'api', 'endpoint', 'service', 'microservice', 'container', 'pod', 'node', 'cluster', 'instance', 'resource', 'metric', 'alert', 'notification']
        
        # Boost technical terms in keywords
        for term in technical_terms:
            if term in question_lower and term not in keywords:
                keywords.insert(0, term)
        
        entities["keywords"] = list(set(keywords))[:15]  # Increased limit for better context
        
        self.logger.debug(f"Extracted entities: {entities}")
        return entities
    
    def _classify_query_regex(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the query type based on complexity and ambiguity.
        
        Args:
            question: User question text
            entities: Extracted entities
            
        Returns:
            Dictionary containing classification results
        """
        question_lower = question.lower()
        
        # Complex queries: multiple services, complex relationships, analysis requests
        has_multiple_services = len(entities.get("services", {})) > 1
        has_analysis_keywords = any(keyword in question_lower for keyword in [
            'analyze', 'compare', 'correlate', 'relationship', 'dependency', 'impact', 'root cause'
        ])
        
        # Check for complex query indicators first (higher priority)
        if has_analysis_keywords or has_multiple_services:
            return {
                "query_type": "complex",
                "confidence": 0.8,
                "reasoning": "Multiple services or analysis keywords detected",
                "complexity_factors": ["multiple_services", "analysis_intent"],
                "missing_information": []
            }
        
        # Ambiguous queries: vague intent, missing critical information
        has_ambiguous_words = any(word in question_lower for word in [
            'something', 'anything', 'everything', 'all', 'some', 'maybe', 'possibly'
        ])
        
        # Simple queries: clear intent, specific service, specific time range
        has_specific_service = len(entities.get("services", {})) == 1
        has_specific_time = len(entities.get("time_indicators", [])) == 1
        has_clear_severity = len(entities.get("severities", [])) == 1
        
        is_vague = len(entities.get("keywords", [])) < 3 and not any([
            has_specific_service, has_specific_time, has_clear_severity
        ])
        
        if is_vague or has_ambiguous_words or (not has_specific_service and not has_specific_time):
            return {
                "query_type": "ambiguous",
                "confidence": 0.9,
                "reasoning": "Vague or ambiguous language detected",
                "complexity_factors": ["vague_intent"],
                "missing_information": ["service_specification", "time_range"]
            }
        else:
            return {
                "query_type": "simple",
                "confidence": 0.7,
                "reasoning": "Clear, specific query with focused intent",
                "complexity_factors": [],
                "missing_information": []
            }
    
    def _detect_missing_info_regex(self, state: AgentState, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect missing information that might be needed for effective investigation.
        
        Args:
            state: Current agent state
            entities: Extracted entities
            
        Returns:
            Dictionary containing missing information analysis
        """
        missing = []
        
        # Check for missing services
        if not entities.get("services") and not state.get("services"):
            missing.append("service_specification")
        
        # Check for missing time range
        if not entities.get("time_indicators") and not state.get("time_range"):
            missing.append("time_range")
        
        # Check for missing severity focus
        if not entities.get("severities"):
            question_lower = state.get("question", "").lower()
            if not any(word in question_lower for word in ["error", "warning", "info", "debug", "fail", "issue"]):
                missing.append("severity_focus")
        
        # Check for project context (already validated as required)
        if not state.get("project_id"):
            missing.append("project_id")
        
        return {
            "missing_information": missing,
            "analysis": f"Rule-based analysis detected {len(missing)} missing information categories",
            "needs_clarification": len(missing) > 0
        }
    
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
