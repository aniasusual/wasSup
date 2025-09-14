"""
LLM Service for the GCP Log Investigation Agent.

This module provides a centralized LLM service using Google Gemini
for natural language processing tasks including entity extraction,
intent classification, and query understanding.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExtractedEntities(BaseModel):
    """Pydantic model for structured entity extraction output."""
    
    # GCP Services
    services: List[str] = Field(
        default_factory=list, 
        description="List of GCP services mentioned (e.g., cloud_run, cloud_sql, gce_instance)"
    )
    
    # Severity levels
    severities: List[str] = Field(
        default_factory=list,
        description="Log severity levels mentioned (ERROR, WARNING, INFO, DEBUG)"
    )
    
    # Time indicators
    time_indicators: List[str] = Field(
        default_factory=list,
        description="Time-related expressions (last_hour, last_day, yesterday, etc.)"
    )
    
    # Error patterns
    error_patterns: List[str] = Field(
        default_factory=list,
        description="Error types or patterns mentioned (authentication, timeout, connection, etc.)"
    )
    
    # HTTP status codes
    http_status_codes: List[str] = Field(
        default_factory=list,
        description="HTTP status codes mentioned (4xx, 5xx, specific codes)"
    )
    
    # Resource identifiers
    resource_identifiers: List[str] = Field(
        default_factory=list,
        description="Specific resource names, IDs, or identifiers mentioned"
    )
    
    # Keywords
    keywords: List[str] = Field(
        default_factory=list,
        description="Important keywords and concepts (performance, latency, failure, etc.)"
    )
    
    # Intent indicators
    intent_indicators: List[str] = Field(
        default_factory=list,
        description="Intent-related words (analyze, compare, investigate, troubleshoot, etc.)"
    )


class QueryClassification(BaseModel):
    """Pydantic model for query classification output."""
    
    query_type: str = Field(
        description="Type of query: 'simple', 'complex', or 'ambiguous'"
    )
    
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence level in the classification (0.0 to 1.0)"
    )
    
    reasoning: str = Field(
        description="Brief explanation of why this classification was chosen"
    )
    
    complexity_factors: List[str] = Field(
        default_factory=list,
        description="Factors that contribute to query complexity"
    )
    
    missing_information: List[str] = Field(
        default_factory=list,
        description="Information that might be missing for effective investigation"
    )
    
    needs_clarification: bool = Field(
        default=False,
        description="Whether the query needs clarification before proceeding"
    )
    
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Specific questions to ask for clarification"
    )
    
    suggested_scope: str = Field(
        default="",
        description="Suggested scope for the investigation based on the query"
    )


class LLMService:
    """
    Centralized LLM service for natural language processing tasks.
    
    Uses Google Gemini for entity extraction, intent classification,
    and query understanding in the GCP log investigation context.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            api_key: Google Gemini API key (if not provided, uses environment variable)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. LLM features will be disabled.")
            self.llm = None
        else:
            # Initialize Gemini model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.1,  # Low temperature for consistent extraction
                max_output_tokens=2048,
                convert_system_message_to_human=True
            )
            
            # Initialize output parsers
            self.entity_parser = JsonOutputParser(pydantic_object=ExtractedEntities)
            self.classification_parser = JsonOutputParser(pydantic_object=QueryClassification)
            
            logger.info("LLM service initialized with Gemini 1.5 Flash")
    
    def _create_entity_extraction_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for entity extraction."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing GCP (Google Cloud Platform) log investigation queries. 
Your task is to extract structured information from user queries about GCP services, logs, and troubleshooting.

Focus on identifying:
1. GCP Services: cloud_run, cloud_sql, gce_instance, gke_cluster, app_engine, cloud_functions, load_balancer, cloud_storage, etc.
2. Severity Levels: ERROR, WARNING, INFO, DEBUG
3. Time Indicators: last_hour, last_day, yesterday, recent, etc.
4. Error Patterns: authentication, timeout, connection, database, memory, cpu, etc.
5. HTTP Status Codes: 4xx, 5xx, or specific codes like 404, 500, etc.
6. Resource Identifiers: service names, instance IDs, cluster names, etc.
7. Keywords: performance, latency, failure, issue, problem, etc.
8. Intent Indicators: analyze, compare, investigate, troubleshoot, find, show, etc.

Be precise and only include entities that are explicitly mentioned or strongly implied in the query."""),
            
            ("human", """Extract entities from this GCP log investigation query:

Query: "{question}"

{format_instructions}

Provide your analysis in the specified JSON format.""")
        ])
        
        return prompt
    
    def _create_classification_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for query classification."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at classifying GCP log investigation queries and determining what information is needed for effective investigation.

Classify queries into three categories:

SIMPLE QUERIES:
- Clear, specific intent with focused scope
- Single service or resource type clearly identified
- Specific time range or timeframe mentioned
- Straightforward log filtering needs
- Example: "Show me errors from cloud_run service in the last hour"

COMPLEX QUERIES:
- Multiple services or resources involved
- Relationship analysis between components
- Root cause investigation across systems
- Performance analysis and correlation
- Cross-service impact assessment
- Example: "Analyze the relationship between cloud_run and cloud_sql failures"

AMBIGUOUS QUERIES:
- Vague or unclear intent
- Missing critical information (services, time range, error types, etc.)
- Too broad or general scope
- Need clarification to proceed effectively
- Example: "Something is wrong with my application"

For each query, also determine:
1. What information might be missing for effective investigation
2. Whether clarification is needed before proceeding
3. Specific questions to ask for clarification if needed
4. Suggested scope for the investigation

Focus on practical GCP log investigation needs and provide actionable insights."""),
            
            ("human", """Classify this GCP log investigation query and determine clarification needs:

Query: "{question}"
Extracted Entities: {entities}

{format_instructions}

Provide your analysis in the specified JSON format.""")
        ])
        
        return prompt
    
    async def extract_entities(self, question: str) -> Dict[str, Any]:
        """
        Extract entities from a user query using LLM.
        
        Args:
            question: User's question about GCP logs
            
        Returns:
            Dictionary containing extracted entities
        """
        if not self.llm:
            logger.warning("LLM not available, falling back to basic extraction")
            return self._fallback_entity_extraction(question)
        
        try:
            prompt = self._create_entity_extraction_prompt()
            chain = prompt | self.llm | self.entity_parser
            
            # Add format instructions to the prompt
            format_instructions = self.entity_parser.get_format_instructions()
            
            result = await chain.ainvoke({
                "question": question,
                "format_instructions": format_instructions
            })
            
            logger.debug(f"LLM extracted entities: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {str(e)}")
            logger.info("Falling back to basic extraction")
            return self._fallback_entity_extraction(question)
    
    async def classify_query(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a query using LLM.
        
        Args:
            question: User's question
            entities: Extracted entities
            
        Returns:
            Dictionary containing classification results
        """
        if not self.llm:
            logger.warning("LLM not available, falling back to basic classification")
            return self._fallback_query_classification(question, entities)
        
        try:
            prompt = self._create_classification_prompt()
            chain = prompt | self.llm | self.classification_parser
            
            # Add format instructions to the prompt
            format_instructions = self.classification_parser.get_format_instructions()
            
            result = await chain.ainvoke({
                "question": question,
                "entities": json.dumps(entities, indent=2, default=str),
                "format_instructions": format_instructions
            })
            
            logger.debug(f"LLM classified query: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM query classification: {str(e)}")
            logger.info("Falling back to basic classification")
            return self._fallback_query_classification(question, entities)
    
    async def detect_missing_information(self, question: str, entities: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently detect missing information needed for effective investigation.
        
        Args:
            question: User's question
            entities: Extracted entities
            state: Current agent state
            
        Returns:
            Dictionary containing missing information analysis
        """
        if not self.llm:
            logger.warning("LLM not available, falling back to basic missing info detection")
            return self._fallback_missing_info_detection(question, entities, state)
        
        try:
            # Create a specialized prompt for missing information detection
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at analyzing GCP log investigation queries to determine what information might be missing for effective troubleshooting.

For GCP log investigations, consider what information is typically needed:
1. Service/Resource identification (cloud_run, cloud_sql, gce_instance, etc.)
2. Time range or timeframe (last hour, yesterday, specific dates)
3. Severity levels (ERROR, WARNING, INFO, DEBUG)
4. Error patterns or types (authentication, timeout, connection, performance)
5. Specific resource identifiers (service names, instance IDs)
6. Investigation scope (single service vs multi-service)

Analyze the query and entities to determine what might be missing or unclear."""),
                
                ("human", """Analyze this GCP log investigation query for missing information:

Query: "{question}"
Extracted Entities: {entities}
Current State: {state}

Determine what information might be missing for effective investigation. Consider:
- Is the service/resource clearly identified?
- Is the time range specified?
- Are severity levels or error types mentioned?
- Is the scope of investigation clear?
- Are there any ambiguities that need clarification?

Provide your analysis focusing on practical investigation needs.""")
            ])
            
            # Use a simple string output parser for this task
            chain = prompt | self.llm | StrOutputParser()
            
            # Serialize state safely (handle datetime objects recursively)
            def serialize_datetime_objects(obj):
                """Recursively serialize datetime objects in nested structures."""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(obj, 'isoformat'):  # Handle other datetime-like objects
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_datetime_objects(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_datetime_objects(item) for item in obj]
                else:
                    return obj
            
            safe_state = serialize_datetime_objects(state)
            
            result = await chain.ainvoke({
                "question": question,
                "entities": json.dumps(entities, indent=2, default=str),
                "state": json.dumps(safe_state, indent=2, default=str)
            })
            
            # Parse the result to extract missing information
            missing_info = self._parse_missing_info_result(result)
            
            logger.debug(f"LLM detected missing information: {missing_info}")
            return missing_info
            
        except Exception as e:
            logger.error(f"Error in LLM missing info detection: {str(e)}")
            logger.info("Falling back to basic detection")
            return self._fallback_missing_info_detection(question, entities, state)
    
    def _parse_missing_info_result(self, result: str) -> Dict[str, Any]:
        """Parse the LLM result for missing information detection."""
        missing_info = []
        
        # Convert LLM response to structured missing information
        result_lower = result.lower()
        
        if "service" in result_lower and ("not specified" in result_lower or "missing" in result_lower):
            missing_info.append("service_specification")
        
        if "time" in result_lower and ("range" in result_lower or "timeframe" in result_lower):
            if "not specified" in result_lower or "missing" in result_lower:
                missing_info.append("time_range")
        
        if "severity" in result_lower or "error" in result_lower:
            if "not specified" in result_lower or "missing" in result_lower:
                missing_info.append("severity_focus")
        
        if "scope" in result_lower and ("unclear" in result_lower or "ambiguous" in result_lower):
            missing_info.append("investigation_scope")
        
        return {
            "missing_information": missing_info,
            "analysis": result,
            "needs_clarification": len(missing_info) > 0
        }
    
    def _fallback_entity_extraction(self, question: str) -> Dict[str, Any]:
        """
        Fallback entity extraction using regex patterns.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary containing extracted entities
        """
        import re
        
        question_lower = question.lower()
        
        # Service patterns
        service_patterns = {
            'cloud_run': r'\b(?:cloud.?run|cloudrun|run)\b',
            'cloud_sql': r'\b(?:cloud.?sql|cloudsql|sql)\b',
            'gce_instance': r'\b(?:gce|compute.?engine|compute.?instance|vm|instance)\b',
            'gke_cluster': r'\b(?:gke|kubernetes|k8s|cluster)\b',
            'app_engine': r'\b(?:app.?engine|gae)\b',
            'cloud_functions': r'\b(?:cloud.?functions|functions|gcf)\b',
            'load_balancer': r'\b(?:load.?balancer|lb|ingress)\b',
            'cloud_storage': r'\b(?:cloud.?storage|storage|gcs|bucket)\b'
        }
        
        # Extract services
        services = []
        for service_name, pattern in service_patterns.items():
            if re.search(pattern, question_lower):
                services.append(service_name)
        
        # Extract severities
        severity_patterns = {
            'ERROR': r'\b(?:error|err|failed|failure|exception|critical|fatal)\b',
            'WARNING': r'\b(?:warning|warn|caution|alert)\b',
            'INFO': r'\b(?:info|information|debug|trace)\b'
        }
        
        severities = []
        for severity, pattern in severity_patterns.items():
            if re.search(pattern, question_lower):
                severities.append(severity)
        
        # Extract time indicators
        time_patterns = {
            'last_hour': r'\b(?:last.?hour|past.?hour|hour)\b',
            'last_day': r'\b(?:last.?day|past.?day|day|yesterday)\b',
            'last_week': r'\b(?:last.?week|past.?week|week)\b',
            'recent': r'\b(?:recent|recently|lately)\b'
        }
        
        time_indicators = []
        for time_type, pattern in time_patterns.items():
            if re.search(pattern, question_lower):
                time_indicators.append(time_type)
        
        # Extract keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question_lower)
        keywords = list(set([word for word in words if word not in stop_words]))[:10]
        
        return {
            "services": services,
            "severities": severities,
            "time_indicators": time_indicators,
            "error_patterns": [],
            "http_status_codes": re.findall(r'\b(?:5\d{2}|4\d{2})\b', question),
            "resource_identifiers": [],
            "keywords": keywords,
            "intent_indicators": []
        }
    
    def _fallback_query_classification(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback query classification using rule-based approach.
        
        Args:
            question: User's question
            entities: Extracted entities
            
        Returns:
            Dictionary containing classification results
        """
        question_lower = question.lower()
        
        # Complex query indicators
        has_multiple_services = len(entities.get("services", [])) > 1
        has_analysis_keywords = any(keyword in question_lower for keyword in [
            'analyze', 'compare', 'correlate', 'relationship', 'dependency', 'impact', 'root cause'
        ])
        
        # Ambiguous query indicators
        has_ambiguous_words = any(word in question_lower for word in [
            'something', 'anything', 'everything', 'all', 'some', 'maybe', 'possibly'
        ])
        
        is_vague = len(entities.get("keywords", [])) < 3 and not any([
            len(entities.get("services", [])) == 1,
            len(entities.get("time_indicators", [])) == 1,
            len(entities.get("severities", [])) == 1
        ])
        
        if has_analysis_keywords or has_multiple_services:
            return {
                "query_type": "complex",
                "confidence": 0.8,
                "reasoning": "Multiple services or analysis keywords detected",
                "complexity_factors": ["multiple_services", "analysis_intent"],
                "missing_information": []
            }
        elif is_vague or has_ambiguous_words:
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
    
    def _fallback_missing_info_detection(self, question: str, entities: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback missing information detection using rule-based approach.
        
        Args:
            question: User's question
            entities: Extracted entities
            state: Current agent state
            
        Returns:
            Dictionary containing missing information analysis
        """
        missing_info = []
        
        # Check for missing services
        if not entities.get("services") and not state.get("services"):
            missing_info.append("service_specification")
        
        # Check for missing time range
        if not entities.get("time_indicators") and not state.get("time_range"):
            missing_info.append("time_range")
        
        # Check for missing severity focus
        if not entities.get("severities"):
            question_lower = question.lower()
            if not any(word in question_lower for word in ["error", "warning", "info", "debug", "fail", "issue"]):
                missing_info.append("severity_focus")
        
        # Check for project context
        if not state.get("project_id"):
            missing_info.append("project_id")
        
        return {
            "missing_information": missing_info,
            "analysis": f"Rule-based analysis detected {len(missing_info)} missing information categories",
            "needs_clarification": len(missing_info) > 0
        }
