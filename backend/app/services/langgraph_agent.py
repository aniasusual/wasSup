from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict, Tuple
import os
import asyncio
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from difflib import SequenceMatcher
import unicodedata

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from langgraph.graph import StateGraph, END

from .conversation_manager import conversation_manager, Message
from .gcp_log_fetcher import GCPLogFetcher
from .gcp_resource_discovery import GCPResourceDiscovery
from .vector_store import QdrantVectorStore


class AgentState(TypedDict):
    """State object for the LangGraph agent."""
    # User inputs
    question: str
    project_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    services: Optional[List[str]]
    time_range: Optional[Dict[str, str]]
    collection: Optional[str]
    limit: int
    access_token: Optional[str]
    
    # Agent state
    current_step: str
    needs_clarification: bool
    missing_info: List[str]
    investigation_context: Dict[str, Any]
    conversation_context: Dict[str, Any]  # Track what we know from conversation
    
    # Results
    analysis: str
    tool_results: Optional[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    relevant_logs: List[Dict[str, Any]]
    clarifying_questions: List[Dict[str, str]]
    
    # Conversation
    conversation_history: List[Dict[str, Any]]
    context_summary: str
    error: Optional[str]


class InvestigationStep(str, Enum):
    """Enumeration of investigation steps."""
    INTELLIGENT_ANALYSIS = "intelligent_analysis"
    CONTEXT_RETRIEVAL = "context_retrieval"
    LOG_ANALYSIS = "log_analysis"
    SMART_CLARIFICATION = "smart_clarification"
    ACTION_GENERATION = "action_generation"
    COMPLETE = "complete"


class RobustTextParser:
    """
    Enterprise-grade text parser with advanced NLP capabilities.
    Handles natural language variations, fuzzy matching, and context understanding.
    """
    
    def __init__(self):
        # Service patterns with fuzzy matching support
        self.service_patterns = {
            "cloud_run_revision": [
                "cloud run", "cloud_run", "cloudrun", "run", "cloud run revision",
                "cloud run service", "cloud run container", "serverless container"
            ],
            "gce_instance": [
                "gce", "compute", "instance", "vm", "virtual machine", "compute engine",
                "ec2", "virtual machine instance", "compute instance"
            ],
            "cloud_function": [
                "function", "cloud function", "cloudfunction", "lambda", "serverless function",
                "function as a service", "faas"
            ],
            "gae_app": [
                "app engine", "gae", "appengine", "google app engine", "platform as a service",
                "paas", "web app", "application engine"
            ],
            "k8s_container": [
                "kubernetes", "gke", "container", "k8s", "pod", "deployment",
                "cluster", "orchestration", "container orchestration"
            ],
            "cloud_sql": [
                "sql", "database", "mysql", "postgresql", "cloud sql", "managed database",
                "relational database", "rdbms"
            ],
            "bigquery": [
                "bigquery", "big query", "data warehouse", "analytics", "sql analytics",
                "data lake", "etl", "data processing"
            ]
        }
        
        # Time patterns with natural language variations
        self.time_patterns = {
            "last_hour": [
                "last hour", "past hour", "1 hr", "1 hour", "last 1 hr", "previous hour",
                "within the hour", "this hour", "current hour", "last 60 minutes"
            ],
            "last_24_hours": [
                "last 24 hours", "past day", "24 hours", "24 hrs", "last day", "previous day",
                "within 24 hours", "last 24h", "past 24 hours", "yesterday to now"
            ],
            "this_week": [
                "this week", "last week", "7 days", "past week", "within a week",
                "last 7 days", "past 7 days", "weekly", "this past week"
            ],
            "yesterday": [
                "yesterday", "past day", "previous day", "day before", "last day",
                "yesterday only", "past 24 hours ending yesterday"
            ],
            "last_30_minutes": [
                "last 30 minutes", "30 min", "30 minutes", "past 30 minutes",
                "within 30 minutes", "last half hour", "past half hour"
            ],
            "last_15_minutes": [
                "last 15 minutes", "15 min", "15 minutes", "past 15 minutes",
                "within 15 minutes", "quarter hour", "past quarter hour"
            ]
        }
        
        # Severity patterns with variations
        self.severity_patterns = {
            "ERROR": [
                "error", "errors", "err", "critical", "fatal", "failure", "failed",
                "exception", "exceptions", "crash", "crashed", "abort", "aborted"
            ],
            "WARNING": [
                "warning", "warnings", "warn", "caution", "attention", "notice",
                "deprecated", "deprecation", "deprecated warning"
            ],
            "INFO": [
                "info", "information", "informational", "general", "normal", "standard",
                "regular", "routine", "status", "state"
            ],
            "DEBUG": [
                "debug", "debugging", "development", "dev", "trace", "tracing",
                "verbose", "detailed", "diagnostic"
            ]
        }
        
        # Context keywords for intent recognition
        self.context_keywords = {
            "performance": ["slow", "performance", "latency", "response time", "throughput", "bottleneck"],
            "errors": ["error", "failure", "crash", "exception", "bug", "issue", "problem"],
            "security": ["auth", "authentication", "permission", "access denied", "unauthorized", "security"],
            "deployment": ["deploy", "deployment", "rollout", "release", "version", "update"],
            "connectivity": ["connection", "network", "timeout", "unreachable", "offline", "disconnected"],
            "scaling": ["scale", "scaling", "capacity", "load", "traffic", "concurrent users"]
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing."""
        if not text:
            return ""
        
        # Convert to lowercase and normalize unicode
        normalized = text.lower().strip()
        normalized = unicodedata.normalize('NFKC', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def fuzzy_match(self, text: str, patterns: List[str], threshold: float = 0.8) -> List[Tuple[str, float]]:
        """Perform fuzzy matching with confidence scores."""
        if not text or not patterns:
            return []
        
        matches = []
        normalized_text = self.normalize_text(text)
        
        for pattern in patterns:
            normalized_pattern = self.normalize_text(pattern)
            
            # Exact match
            if normalized_pattern in normalized_text:
                matches.append((pattern, 1.0))
                continue
            
            # Fuzzy match using sequence matcher
            similarity = SequenceMatcher(None, normalized_text, normalized_pattern).ratio()
            if similarity >= threshold:
                matches.append((pattern, similarity))
            
            # Partial match (pattern is contained in text)
            if normalized_pattern in normalized_text or normalized_text in normalized_pattern:
                partial_score = min(len(normalized_pattern), len(normalized_text)) / max(len(normalized_pattern), len(normalized_text))
                if partial_score >= threshold:
                    matches.append((pattern, partial_score))
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def extract_services_robust(self, text: str) -> List[Dict[str, Any]]:
        """Extract services with confidence scores and context."""
        if not text:
            return []
        
        extracted_services = []
        normalized_text = self.normalize_text(text)
        
        for service_type, patterns in self.service_patterns.items():
            matches = self.fuzzy_match(normalized_text, patterns, threshold=0.6)
            
            if matches:
                best_match = matches[0]
                confidence = best_match[1]
                
                # Boost confidence for exact matches
                if confidence > 0.9:
                    confidence = min(1.0, confidence + 0.1)
                
                extracted_services.append({
                    "type": service_type,
                    "confidence": confidence,
                    "matched_pattern": best_match[0],
                    "context": self._extract_service_context(normalized_text, best_match[0])
                })
        
        # Sort by confidence and remove duplicates
        extracted_services.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Remove lower confidence duplicates of the same service type
        seen_types = set()
        unique_services = []
        for service in extracted_services:
            if service["type"] not in seen_types:
                seen_types.add(service["type"])
                unique_services.append(service)
        
        return unique_services
    
    def extract_time_range_robust(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract time range with confidence and natural language support."""
        if not text:
            return None
        
        normalized_text = self.normalize_text(text)
        now = datetime.utcnow()
        
        # Try exact pattern matching first
        for time_type, patterns in self.time_patterns.items():
            matches = self.fuzzy_match(normalized_text, patterns, threshold=0.7)
            
            if matches:
                best_match = matches[0]
                confidence = best_match[1]
                
                time_info = self._generate_time_range(time_type, now)
                if time_info:
                    time_info["confidence"] = confidence
                    time_info["matched_pattern"] = best_match[0]
                    time_info["extraction_method"] = "pattern_matching"
                    return time_info
        
        # Try relative time expressions
        relative_time = self._extract_relative_time(normalized_text, now)
        if relative_time:
            return relative_time
        
        # Try absolute time expressions
        absolute_time = self._extract_absolute_time(normalized_text, now)
        if absolute_time:
            return absolute_time
        
        return None
    
    def extract_severity_robust(self, text: str) -> List[Dict[str, Any]]:
        """Extract severity levels with confidence scores."""
        if not text:
            return []
        
        extracted_severities = []
        normalized_text = self.normalize_text(text)
        
        for severity_level, patterns in self.severity_patterns.items():
            matches = self.fuzzy_match(normalized_text, patterns, threshold=0.7)
            
            if matches:
                best_match = matches[0]
                confidence = best_match[1]
                
                extracted_severities.append({
                    "level": severity_level,
                    "confidence": confidence,
                    "matched_pattern": best_match[0],
                    "context": self._extract_severity_context(normalized_text, best_match[0])
                })
        
        # Sort by confidence
        extracted_severities.sort(key=lambda x: x["confidence"], reverse=True)
        return extracted_severities
    
    def extract_intent_robust(self, text: str) -> Dict[str, Any]:
        """Extract user intent and context from text."""
        if not text:
            return {"primary_intent": "unknown", "confidence": 0.0, "context": {}}
        
        normalized_text = self.normalize_text(text)
        intent_scores = {}
        
        # Score each intent category
        for intent, keywords in self.context_keywords.items():
            score = 0.0
            keyword_matches = []
            
            for keyword in keywords:
                if keyword in normalized_text:
                    score += 1.0
                    keyword_matches.append(keyword)
            
            if score > 0:
                intent_scores[intent] = {
                    "score": score,
                    "keywords": keyword_matches,
                    "confidence": min(1.0, score / len(keywords))
                }
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k]["score"])
            primary_confidence = intent_scores[primary_intent]["confidence"]
        else:
            primary_intent = "general_inquiry"
            primary_confidence = 0.5
        
        return {
            "primary_intent": primary_intent,
            "confidence": primary_confidence,
            "context": intent_scores,
            "all_intents": intent_scores
        }
    
    def _extract_service_context(self, text: str, matched_pattern: str) -> Dict[str, Any]:
        """Extract context around service mentions."""
        context = {}
        
        # Look for modifiers
        modifiers = ["production", "staging", "development", "test", "canary", "blue", "green"]
        for modifier in modifiers:
            if modifier in text:
                context["environment"] = modifier
        
        # Look for specific instances
        instance_pattern = r'(\w+)-(\d+)'
        instances = re.findall(instance_pattern, text)
        if instances:
            context["instances"] = instances
        
        return context
    
    def _extract_severity_context(self, text: str, matched_pattern: str) -> Dict[str, Any]:
        """Extract context around severity mentions."""
        context = {}
        
        # Look for frequency indicators
        frequency_patterns = ["only", "just", "all", "including", "exclude", "filter"]
        for pattern in frequency_patterns:
            if pattern in text:
                context["frequency_filter"] = pattern
        
        return context
    
    def _generate_time_range(self, time_type: str, now: datetime) -> Optional[Dict[str, Any]]:
        """Generate time range based on type."""
        if time_type == "last_hour":
            start_time = now - timedelta(hours=1)
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": "last hour",
                "duration_minutes": 60
            }
        elif time_type == "last_24_hours":
            start_time = now - timedelta(days=1)
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": "last 24 hours",
                "duration_minutes": 1440
            }
        elif time_type == "this_week":
            start_time = now - timedelta(days=7)
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": "this week",
                "duration_minutes": 10080
            }
        elif time_type == "yesterday":
            start_time = now - timedelta(days=1)
            end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "description": "yesterday",
                "duration_minutes": 1440
            }
        elif time_type == "last_30_minutes":
            start_time = now - timedelta(minutes=30)
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": "last 30 minutes",
                "duration_minutes": 30
            }
        elif time_type == "last_15_minutes":
            start_time = now - timedelta(minutes=15)
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": "last 15 minutes",
                "duration_minutes": 15
            }
        
        return None
    
    def _extract_relative_time(self, text: str, now: datetime) -> Optional[Dict[str, Any]]:
        """Extract relative time expressions."""
        # Handle "X minutes ago", "X hours ago", etc.
        relative_patterns = [
            (r'(\d+)\s*minutes?\s*ago', lambda m: timedelta(minutes=int(m.group(1)))),
            (r'(\d+)\s*hours?\s*ago', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s*days?\s*ago', lambda m: timedelta(days=int(m.group(1)))),
        ]
        
        for pattern, time_func in relative_patterns:
            match = re.search(pattern, text)
            if match:
                delta = time_func(match)
                start_time = now - delta
                return {
                    "start_time": start_time.isoformat(),
                    "end_time": now.isoformat(),
                    "description": f"last {match.group(1)} {'minute' if 'minute' in pattern else 'hour' if 'hour' in pattern else 'day'}",
                    "extraction_method": "relative_time",
                    "confidence": 0.8
                }
        
        return None
    
    def _extract_absolute_time(self, text: str, now: datetime) -> Optional[Dict[str, Any]]:
        """Extract absolute time expressions."""
        # Handle "since 9 AM", "from 2 PM to 4 PM", etc.
        absolute_patterns = [
            (r'since\s+(\d{1,2})\s*(am|pm)', self._parse_time_since),
            (r'from\s+(\d{1,2})\s*(am|pm)\s+to\s+(\d{1,2})\s*(am|pm)', self._parse_time_range),
        ]
        
        for pattern, parser_func in absolute_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = parser_func(match, now)
                if result:
                    result["extraction_method"] = "absolute_time"
                    result["confidence"] = 0.7
                    return result
        
        return None
    
    def _parse_time_since(self, match, now: datetime) -> Optional[Dict[str, Any]]:
        """Parse 'since X AM/PM' expressions."""
        try:
            hour = int(match.group(1))
            ampm = match.group(2).lower()
            
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            
            start_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if start_time > now:
                start_time = start_time - timedelta(days=1)
            
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": f"since {match.group(1)} {match.group(2).upper()}"
            }
        except:
            return None
    
    def _parse_time_range(self, match, now: datetime) -> Optional[Dict[str, Any]]:
        """Parse 'from X AM to Y PM' expressions."""
        try:
            start_hour = int(match.group(1))
            start_ampm = match.group(2).lower()
            end_hour = int(match.group(3))
            end_ampm = match.group(4).lower()
            
            # Convert to 24-hour format
            if start_ampm == "pm" and start_hour != 12:
                start_hour += 12
            elif start_ampm == "am" and start_hour == 12:
                start_hour = 0
            
            if end_ampm == "pm" and end_hour != 12:
                end_hour += 12
            elif end_ampm == "am" and end_hour == 12:
                end_hour = 0
            
            # Determine if this is today or yesterday
            start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            
            if start_time > end_time:
                # Crosses midnight
                end_time = end_time + timedelta(days=1)
            
            if start_time > now:
                # This is for yesterday
                start_time = start_time - timedelta(days=1)
                end_time = end_time - timedelta(days=1)
            
            return {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "description": f"from {match.group(1)} {match.group(2).upper()} to {match.group(3)} {match.group(4).upper()}"
            }
        except:
            return None


class SmartLangGraphAgent:
    """
    Intelligent LangGraph-based agent that can handle partial information,
    build context incrementally, and make smart decisions about when to proceed.
    """
    
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        self.gcp_log_fetcher = GCPLogFetcher()
        self.gcp_resource_discovery = GCPResourceDiscovery()
        self.vector_store = QdrantVectorStore()
        
        # Initialize the robust text parser
        self.robust_parser = RobustTextParser()
        
        # Initialize Gemini model directly
        self.model = genai.GenerativeModel(
            os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Build the intelligent workflow graph
        self.workflow = self._build_intelligent_workflow()
    
    def _build_intelligent_workflow(self) -> StateGraph:
        """Build an intelligent workflow that can handle partial information."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("intelligent_analysis", self._intelligent_analysis_node)
        workflow.add_node("context_retrieval", self._context_retrieval_node)
        workflow.add_node("log_analysis", self._log_analysis_node)
        workflow.add_node("smart_clarification", self._smart_clarification_node)
        workflow.add_node("action_generation", self._action_generation_node)
        workflow.add_node("complete", self._complete_node)
        
        # Define the intelligent workflow edges
        workflow.set_entry_point("intelligent_analysis")
        
        # Add conditional edges with smart routing
        workflow.add_conditional_edges(
            "intelligent_analysis",
            self._smart_decision_router,
            {
                "proceed_with_analysis": "context_retrieval",
                "need_minimal_clarification": "smart_clarification",
                "proceed_with_partial": "context_retrieval"
            }
        )
        
        workflow.add_edge("context_retrieval", "log_analysis")
        workflow.add_edge("log_analysis", "action_generation")
        workflow.add_edge("action_generation", "complete")
        workflow.add_edge("smart_clarification", "complete")
        
        return workflow.compile()
    
    async def _run_workflow_streaming(self, initial_state: AgentState, yield_updates: bool = False):
        """
        Run the workflow with streaming updates.
        """
        import json
        
        # We'll manually run through each node to provide streaming updates
        state = initial_state.copy()
        
        # Step 1: Intelligent Analysis
        if yield_updates:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing user input...', 'step': 'intelligent_analysis'})}\n\n"
        
        state = await self._intelligent_analysis_node(state)
        
        if yield_updates:
            services = state.get("investigation_context", {}).get("services", [])
            missing = state.get("missing_info", [])
            yield f"data: {json.dumps({'type': 'status', 'message': f'Parsed: Services={services}, Missing={missing}', 'step': 'intelligent_analysis_complete'})}\n\n"
        
        # Step 2: Decision routing
        decision = self._smart_decision_router(state)
        
        if decision == "need_minimal_clarification":
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Generating clarifying questions...', 'step': 'clarification'})}\n\n"
            state = await self._smart_clarification_node(state)
            if yield_updates:
                questions_count = len(state.get("clarifying_questions", []))
                yield f"data: {json.dumps({'type': 'status', 'message': f'Generated {questions_count} clarifying questions', 'step': 'clarification_complete'})}\n\n"
        else:
            # Step 3: Context Retrieval
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Retrieving logs from GCP...', 'step': 'context_retrieval'})}\n\n"
            
            # Handle the streaming context retrieval
            async for update in self._context_retrieval_node_streaming(state, yield_updates):
                if yield_updates:
                    yield update
                # Extract state updates from the context retrieval
                if update.startswith("data: "):
                    try:
                        import json
                        data = json.loads(update[6:])  # Remove "data: " prefix
                        if data.get("type") == "state_update":
                            state = data.get("state", state)
                    except:
                        pass  # Ignore parsing errors for non-state updates
            
            # Step 4: Log Analysis
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing logs with AI...', 'step': 'log_analysis'})}\n\n"
            
            state = await self._log_analysis_node(state)
            
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'AI analysis completed', 'step': 'log_analysis_complete'})}\n\n"
            
            # Step 5: Action Generation
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Generating suggested actions...', 'step': 'action_generation'})}\n\n"
            
            state = await self._action_generation_node(state)
            
            if yield_updates:
                actions_count = len(state.get("actions", []))
                yield f"data: {json.dumps({'type': 'status', 'message': f'Generated {actions_count} actions', 'step': 'action_generation_complete'})}\n\n"
        
        # Step 6: Complete
        if yield_updates:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Finalizing results...', 'step': 'completion'})}\n\n"
        
        state = await self._complete_node(state)
        
        # Return the final state as the last yield
        if yield_updates:
            yield f"data: {json.dumps({'type': 'final_state', 'state': state})}\n\n"
    
    async def analyze_streaming(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        services: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None,
        collection: Optional[str] = None,
        limit: int = 100,
        access_token: Optional[str] = None,
    ):
        """
        Streaming version of analyze that yields progress updates in real-time.
        """
        import json
        
        # Yield initial status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting intelligent analysis...', 'step': 'initialization'})}\n\n"
        
        print(f"🧠 Smart LangGraph Agent: Starting streaming analysis for project_id={project_id}")
        
        # Initialize state with conversation context
        initial_state = AgentState(
            question=question,
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            services=services,
            time_range=time_range,
            collection=collection or f"logs_{project_id}",
            limit=limit,
            access_token=access_token,
            current_step=InvestigationStep.INTELLIGENT_ANALYSIS,
            needs_clarification=False,
            missing_info=[],
            investigation_context={},
            conversation_context={},
            analysis="",
            tool_results=None,
            actions=[],
            relevant_logs=[],
            clarifying_questions=[],
            conversation_history=[],
            context_summary="",
            error=None
        )
        
        # Handle session management and load conversation context
        if not session_id and user_id:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Creating new session...', 'step': 'session_creation'})}\n\n"
            session_id = conversation_manager.create_session(
                user_id=user_id,
                project_id=project_id,
                initial_context={
                    "project_id": project_id,
                    "last_question": question,
                    "analysis_history": []
                }
            )
            initial_state["session_id"] = session_id
        
        # Load existing conversation context if available
        if session_id:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Loading conversation context...', 'step': 'context_loading'})}\n\n"
            session = conversation_manager.get_session(session_id)
            if session:
                initial_state["conversation_context"] = self._extract_conversation_context(session)
        
        # Run the intelligent workflow with streaming updates
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Running intelligent workflow...', 'step': 'workflow_start'})}\n\n"
            
            # We'll need to modify the workflow to support streaming
            final_state = initial_state
            async for update in self._run_workflow_streaming(initial_state, yield_updates=True):
                yield update
                # Check if this is the final state update
                if update.startswith("data: "):
                    try:
                        import json
                        data = json.loads(update[6:])  # Remove "data: " prefix
                        if data.get("type") == "final_state":
                            final_state = data.get("state", initial_state)
                    except:
                        pass  # Ignore parsing errors for non-final-state updates
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Workflow completed successfully', 'step': 'workflow_complete'})}\n\n"
            
            # Format the response
            result = self._format_response(final_state)
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            
        except Exception as e:
            error_msg = f"Error in intelligent LangGraph workflow: {str(e)}"
            print(f"❌ Smart LangGraph Agent: Error: {error_msg}")
            
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            
            result = {
                "analysis": error_msg,
                "toolResults": None,
                "sessionId": session_id,
                "contextSummary": "Error occurred during analysis",
                "actions": [],
                "needsClarification": False,
                "error": str(e)
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"

    async def analyze(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        services: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None,
        collection: Optional[str] = None,
        limit: int = 100,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for the intelligent LangGraph agent.
        """
        print(f"🧠 Smart LangGraph Agent: Starting intelligent analysis for project_id={project_id}")
        
        # Initialize state with conversation context
        initial_state = AgentState(
            question=question,
            project_id=project_id,
            session_id=session_id,
            user_id=user_id,
            services=services,
            time_range=time_range,
            collection=collection or f"logs_{project_id}",
            limit=limit,
            access_token=access_token,
            current_step=InvestigationStep.INTELLIGENT_ANALYSIS,
            needs_clarification=False,
            missing_info=[],
            investigation_context={},
            conversation_context={},
            analysis="",
            tool_results=None,
            actions=[],
            relevant_logs=[],
            clarifying_questions=[],
            conversation_history=[],
            context_summary="",
            error=None
        )
        
        # Handle session management and load conversation context
        if not session_id and user_id:
            session_id = conversation_manager.create_session(
                user_id=user_id,
                project_id=project_id,
                initial_context={
                    "project_id": project_id,
                    "last_question": question,
                    "analysis_history": []
                }
            )
            initial_state["session_id"] = session_id
        
        # Load existing conversation context if available
        if session_id:
            session = conversation_manager.get_session(session_id)
            if session:
                initial_state["conversation_context"] = self._extract_conversation_context(session)
        
        # Run the intelligent workflow
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            print(f"🧠 Smart LangGraph Agent: Workflow completed successfully")
            
            # Format the response
            return self._format_response(final_state)
            
        except Exception as e:
            error_msg = f"Error in intelligent LangGraph workflow: {str(e)}"
            print(f"❌ Smart LangGraph Agent: Error: {error_msg}")
            
            return {
                "analysis": error_msg,
                "toolResults": None,
                "sessionId": session_id,
                "contextSummary": "Error occurred during analysis",
                "actions": [],
                "needsClarification": False,
                "error": str(e)
            }
    
    def _extract_conversation_context(self, session) -> Dict[str, Any]:
        """Extract what we already know from the conversation."""
        context = {}
        
        if session.context:
            # Extract previously mentioned services
            if session.context.get("services"):
                context["known_services"] = session.context["services"]
            
            # Extract previously mentioned time ranges
            if session.context.get("time_range"):
                context["known_time_range"] = session.context["time_range"]
            
            # Extract previously mentioned severity levels
            if session.context.get("severity_filters"):
                context["known_severity"] = session.context["severity_filters"]
        
        return context
    
    async def _intelligent_analysis_node(self, state: AgentState) -> AgentState:
        """Intelligently analyze user input and conversation context."""
        print(f"🧠 Smart Agent: Intelligent analysis node")
        
        # Parse the current question intelligently
        parsed_info = self._intelligent_input_parser(
            state["question"], 
            state["conversation_context"]
        )
        
        # Merge with any existing information
        merged_info = self._merge_information(parsed_info, state)
        
        # Update state with intelligent analysis
        state["investigation_context"] = merged_info
        state["missing_info"] = merged_info.get("missing", [])
        state["needs_clarification"] = len(merged_info.get("missing", [])) > 0
        state["current_step"] = InvestigationStep.INTELLIGENT_ANALYSIS
        
        print(f"🧠 Smart Agent: Parsed info: {parsed_info}")
        print(f"🧠 Smart Agent: Missing info: {state['missing_info']}")
        
        return state
    
    def _intelligent_input_parser(self, question: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently parse user input using the robust parser."""
        
        # Use the robust parser for all extractions
        extracted_services = self.robust_parser.extract_services_robust(question)
        extracted_time_range = self.robust_parser.extract_time_range_robust(question)
        extracted_severities = self.robust_parser.extract_severity_robust(question)
        extracted_intent = self.robust_parser.extract_intent_robust(question)
        
        # Convert to the format expected by the rest of the system
        services = [s["type"] for s in extracted_services] if extracted_services else []
        time_range = extracted_time_range if extracted_time_range else None
        severity = [s["level"] for s in extracted_severities] if extracted_severities else None
        
        # Extract search query from intent and question
        search_query = self._extract_search_query_robust(question, extracted_intent)
        
        # Determine what's missing with confidence thresholds
        missing = []
        confidence_threshold = 0.7
        
        if not services or (extracted_services and extracted_services[0]["confidence"] < confidence_threshold):
            missing.append("services")
        if not time_range or (extracted_time_range and extracted_time_range.get("confidence", 0) < confidence_threshold):
            missing.append("time_range")
        if not severity or (extracted_severities and extracted_severities[0]["confidence"] < confidence_threshold):
            missing.append("severity")
        
        # Check if we have enough context to proceed
        has_minimal_context = len(services) > 0 and time_range is not None
        
        # Calculate overall confidence
        confidences = []
        if extracted_services:
            confidences.extend([s["confidence"] for s in extracted_services])
        if extracted_time_range:
            confidences.append(extracted_time_range.get("confidence", 0))
        if extracted_severities:
            confidences.extend([s["confidence"] for s in extracted_severities])
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "services": services,
            "time_range": time_range,
            "severity": severity,
            "search_query": search_query,
            "missing": missing,
            "has_minimal_context": has_minimal_context,
            "can_proceed": has_minimal_context or len(missing) <= 1,
            "confidence": overall_confidence,
            "extraction_details": {
                "services": extracted_services,
                "time_range": extracted_time_range,
                "severity": extracted_severities,
                "intent": extracted_intent
            }
        }
    

    
    def _extract_search_query_robust(self, text: str, intent_info: Dict[str, Any]) -> str:
        """Extract search query using robust parsing and intent recognition."""
        if not text:
            return ""
        
        # Use intent information to build better search queries
        primary_intent = intent_info.get("primary_intent", "general_inquiry")
        intent_context = intent_info.get("context", {})
        
        # Build search query based on intent
        search_terms = []
        
        if primary_intent == "errors":
            search_terms.extend(["error", "exception", "failure", "crash"])
        elif primary_intent == "performance":
            search_terms.extend(["slow", "latency", "timeout", "performance"])
        elif primary_intent == "security":
            search_terms.extend(["auth", "permission", "unauthorized", "access denied"])
        elif primary_intent == "deployment":
            search_terms.extend(["deploy", "rollout", "version", "update"])
        elif primary_intent == "connectivity":
            search_terms.extend(["connection", "network", "timeout", "unreachable"])
        elif primary_intent == "scaling":
            search_terms.extend(["scale", "capacity", "load", "traffic"])
        
        # Add specific keywords from the text
        specific_keywords = [
            "issue", "issues", "problem", "problems", "bug", "incident",
            "outage", "downtime", "degradation", "failure", "error",
            "exception", "crash", "timeout", "slow", "performance",
            "authentication", "auth", "login", "permission", "access denied",
            "database", "db", "connection", "network", "api", "service",
            "deployment", "deploy", "rollout", "version", "update",
            "monitoring", "alert", "alarm", "metric", "log"
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in specific_keywords if kw in text_lower]
        
        # Combine intent-based and specific keywords
        all_terms = list(set(search_terms + found_keywords))
        
        if all_terms:
            # Use the most relevant terms (limit to 5 for performance)
            relevant_terms = all_terms[:5]
            return " OR ".join(relevant_terms)
        
        # Fallback: use the question as search query
        return text.strip()
    
    def _merge_information(self, parsed_info: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Merge parsed information with existing context."""
        merged = parsed_info.copy()
        
        # Merge with existing services
        if state.get("services") and not merged["services"]:
            merged["services"] = state["services"]
        
        # Merge with existing time range
        if state.get("time_range") and not merged["time_range"]:
            merged["time_range"] = state["time_range"]
        
        # Merge with conversation context
        if state.get("conversation_context"):
            conv_context = state["conversation_context"]
            
            if not merged["services"] and conv_context.get("known_services"):
                merged["services"] = conv_context["known_services"]
            
            if not merged["time_range"] and conv_context.get("known_time_range"):
                merged["time_range"] = conv_context["known_time_range"]
            
            if not merged["severity"] and conv_context.get("known_severity"):
                merged["severity"] = conv_context["known_severity"]
        
        # Re-evaluate what's missing
        missing = []
        if not merged["services"]:
            missing.append("services")
        if not merged["time_range"]:
            missing.append("time_range")
        if not merged["severity"]:
            missing.append("severity")
        
        merged["missing"] = missing
        
        # Safe length checks with None handling
        services_count = len(merged["services"]) if merged["services"] else 0
        time_range_exists = merged["time_range"] is not None
        
        merged["has_minimal_context"] = services_count > 0 and time_range_exists
        merged["can_proceed"] = merged["has_minimal_context"] or len(missing) <= 1
        
        return merged
    
    def _smart_decision_router(self, state: AgentState) -> str:
        """Make intelligent decisions about workflow routing."""
        context = state["investigation_context"]
        
        if context.get("can_proceed", False):
            if context.get("has_minimal_context", False):
                return "proceed_with_analysis"
            else:
                return "proceed_with_partial"
        else:
            return "need_minimal_clarification"
    
    async def _context_retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant context and logs using GCP Logging API with fallback strategies."""
        print(f"🧠 Smart Agent: Context retrieval node")
        
        try:
            context = state["investigation_context"]
            
            # Get available resources if we have an access token
            if state["access_token"]:
                available_resources = await self.gcp_resource_discovery.get_resource_summary(
                    state["project_id"], 
                    state["access_token"]
                )
                state["investigation_context"]["available_resources"] = available_resources
            
            # Build GCP Logging filter from parsed context
            filter_str = self._build_gcp_logging_filter(context, state["project_id"])
            
            # Fetch logs using GCP Logging REST API (same as logs.py route)
            retrieved_logs = await self._fetch_logs_from_gcp(
                project_id=state["project_id"],
                filter_str=filter_str,
                access_token=state["access_token"],
                limit=state["limit"]
            )
            
            # If no logs found, try fallback strategies
            if not retrieved_logs:
                print(f"🧠 Smart Agent: No logs found with primary filter, trying fallback strategies...")
                
                # Fallback 1: Remove severity filter
                if context.get("severity"):
                    fallback_context = context.copy()
                    fallback_context.pop("severity", None)
                    fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (no severity): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                # Fallback 2: Remove text search filter
                if not retrieved_logs and context.get("search_query"):
                    fallback_context = context.copy()
                    fallback_context.pop("search_query", None)
                    fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (no text search): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                # Fallback 3: Use only resource type
                if not retrieved_logs and context.get("services"):
                    fallback_context = {"services": context["services"]}
                    fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (services only): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                # Fallback 4: Use default filter (last 7 days)
                if not retrieved_logs:
                    fallback_filter = self._build_gcp_logging_filter({}, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (default): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
            
            state["relevant_logs"] = self._format_logs_for_ui(retrieved_logs)
            state["investigation_context"]["retrieved_logs"] = retrieved_logs
            state["investigation_context"]["filter_applied"] = filter_str
            state["current_step"] = InvestigationStep.CONTEXT_RETRIEVAL
            
            print(f"🧠 Smart Agent: Retrieved {len(retrieved_logs)} logs using GCP Logging API")
            
        except Exception as e:
            state["error"] = f"Error retrieving context: {str(e)}"
            print(f"❌ Smart Agent: Context retrieval error: {str(e)}")
        
        return state
    
    async def _context_retrieval_node_streaming(self, state: AgentState, yield_updates: bool = False) -> AgentState:
        """Retrieve relevant context and logs using GCP Logging API with streaming updates."""
        import json
        
        if yield_updates:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting context retrieval...', 'step': 'context_retrieval_start'})}\n\n"
        
        print(f"🧠 Smart Agent: Context retrieval node")
        
        try:
            context = state["investigation_context"]
            
            # Get available resources if we have an access token
            if state["access_token"]:
                if yield_updates:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Discovering available GCP resources...', 'step': 'resource_discovery'})}\n\n"
                
                available_resources = await self.gcp_resource_discovery.get_resource_summary(
                    state["project_id"], 
                    state["access_token"]
                )
                state["investigation_context"]["available_resources"] = available_resources
                
                if yield_updates:
                    resource_count = len(available_resources.get("summary", {}))
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Discovered {resource_count} resource types', 'step': 'resource_discovery_complete'})}\n\n"
            
            # Build GCP Logging filter from parsed context
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Building GCP log filter...', 'step': 'filter_building'})}\n\n"
            
            filter_str = self._build_gcp_logging_filter(context, state["project_id"])
            
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': f'Filter: {filter_str[:100]}...', 'step': 'filter_built'})}\n\n"
            
            # Fetch logs using GCP Logging REST API (same as logs.py route)
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Fetching logs from GCP...', 'step': 'log_fetching'})}\n\n"
            
            retrieved_logs = await self._fetch_logs_from_gcp(
                project_id=state["project_id"],
                filter_str=filter_str,
                access_token=state["access_token"],
                limit=state["limit"]
            )
            
            if yield_updates:
                logs_count = len(retrieved_logs)
                yield f"data: {json.dumps({'type': 'status', 'message': f'Retrieved {logs_count} logs', 'step': 'log_fetching_complete'})}\n\n"
            
            # If no logs found, try fallback strategies
            if not retrieved_logs:
                if yield_updates:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'No logs found, trying fallback strategies...', 'step': 'fallback_start'})}\n\n"
                
                print(f"🧠 Smart Agent: No logs found with primary filter, trying fallback strategies...")
                
                # Fallback 1: Remove severity filter
                if context.get("severity"):
                    if yield_updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': 'Trying fallback: removing severity filter...', 'step': 'fallback_1'})}\n\n"
                    
                    fallback_context = context.copy()
                    fallback_context.pop("severity", None)
                    fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (no severity): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                # Fallback 2: Remove text search filter
                if not retrieved_logs and context.get("search_query"):
                    if yield_updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': 'Trying fallback: removing text search...', 'step': 'fallback_2'})}\n\n"
                    
                    fallback_context = context.copy()
                    fallback_context.pop("search_query", None)
                    fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (no text search): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                # Fallback 3: Use only resource type
                if not retrieved_logs and context.get("services"):
                    if yield_updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': 'Trying fallback: services only...', 'step': 'fallback_3'})}\n\n"
                    
                    fallback_context = {"services": context["services"]}
                    fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (services only): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                # Fallback 4: Use default filter (last 7 days)
                if not retrieved_logs:
                    if yield_updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': 'Trying fallback: default filter...', 'step': 'fallback_4'})}\n\n"
                    
                    fallback_filter = self._build_gcp_logging_filter({}, state["project_id"])
                    print(f"🧠 Smart Agent: Trying fallback filter (default): {fallback_filter}")
                    
                    retrieved_logs = await self._fetch_logs_from_gcp(
                        project_id=state["project_id"],
                        filter_str=fallback_filter,
                        access_token=state["access_token"],
                        limit=state["limit"]
                    )
                
                if yield_updates:
                    fallback_logs_count = len(retrieved_logs)
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Fallback complete: {fallback_logs_count} logs found', 'step': 'fallback_complete'})}\n\n"
            
            state["relevant_logs"] = self._format_logs_for_ui(retrieved_logs)
            state["investigation_context"]["retrieved_logs"] = retrieved_logs
            state["investigation_context"]["filter_applied"] = filter_str
            state["current_step"] = InvestigationStep.CONTEXT_RETRIEVAL
            
            print(f"🧠 Smart Agent: Retrieved {len(retrieved_logs)} logs using GCP Logging API")
            
            if yield_updates:
                final_logs_count = len(retrieved_logs)
                yield f"data: {json.dumps({'type': 'status', 'message': f'Context retrieval complete: {final_logs_count} logs ready for analysis', 'step': 'context_retrieval_complete'})}\n\n"
            
        except Exception as e:
            state["error"] = f"Error retrieving context: {str(e)}"
            print(f"❌ Smart Agent: Context retrieval error: {str(e)}")
            
            if yield_updates:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Context retrieval error: {str(e)}', 'step': 'context_retrieval_error'})}\n\n"
        
        # Return the state by yielding it as the final update
        if yield_updates:
            yield f"data: {json.dumps({'type': 'state_update', 'state': state})}\n\n"
    
    def _build_gcp_logging_filter(self, context: Dict[str, Any], project_id: str) -> str:
        """Build GCP Logging filter string from parsed context - matches logs.py format."""
        filter_parts = []
        
        # Add resource type filter if services are specified
        if context.get("services"):
            service_filters = []
            for service in context["services"]:
                service_filters.append(f'resource.type="{service}"')
            
            if len(service_filters) == 1:
                filter_parts.append(service_filters[0])
            else:
                filter_parts.append(f"({' OR '.join(service_filters)})")
        
        # Add severity filter if specified
        if context.get("severity"):
            severity_filters = []
            for severity in context["severity"]:
                severity_filters.append(f'severity="{severity}"')
            
            if len(severity_filters) == 1:
                filter_parts.append(severity_filters[0])
            else:
                filter_parts.append(f"({' OR '.join(severity_filters)})")
        
        # Add time range filter if specified
        if context.get("time_range"):
            time_range = context["time_range"]
            start_time = time_range.get("start_time")
            end_time = time_range.get("end_time")
            
            if start_time and end_time:
                # Convert ISO format to RFC 3339 format for GCP Logging API
                # GCP expects format like: 2024-01-01T00:00:00Z or 2024-01-01T00:00:00.000Z
                def format_timestamp_for_gcp(ts):
                    if not ts:
                        return ts
                    
                    # Remove microseconds if present and add .000Z
                    if '.' in ts and 'Z' not in ts:
                        # Keep only 3 digits of microseconds
                        parts = ts.split('.')
                        if len(parts) == 2:
                            base_time = parts[0]
                            microseconds = parts[1][:3]  # Truncate to 3 digits
                            ts = f"{base_time}.{microseconds}Z"
                    elif not ts.endswith('Z') and '+' not in ts:
                        ts += 'Z'
                    
                    return ts
                
                start_timestamp = format_timestamp_for_gcp(start_time)
                end_timestamp = format_timestamp_for_gcp(end_time)
                
                filter_parts.append(f'timestamp>="{start_timestamp}" AND timestamp<="{end_timestamp}"')
        
        # Add text search filter if search query is available
        if context.get("search_query"):
            search_query = context["search_query"]
            # Escape quotes and wrap in textPayload search
            escaped_query = search_query.replace('"', '\\"')
            filter_parts.append(f'textPayload:"{escaped_query}"')
        
        # Combine all filters with AND
        if filter_parts:
            return " AND ".join(filter_parts)
        else:
            # Default filter for recent logs if no specific filters - use a broader time range
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            return f'timestamp>="{week_ago.isoformat()}Z"'
    
    async def _fetch_logs_from_gcp(
        self, 
        project_id: str, 
        filter_str: str, 
        access_token: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch logs from GCP Logging API using the exact same method as logs.py route."""
        import requests
        from concurrent.futures import ThreadPoolExecutor
        
        def fetch_logs_sync():
            try:
                url = "https://logging.googleapis.com/v2/entries:list"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                body = {
                    "resourceNames": [f"projects/{project_id}"],
                    "filter": filter_str,
                    "orderBy": "timestamp desc",
                    "pageSize": min(limit, 1000),  # Cap at 1000 for performance
                }
                
                print(f"🧠 Smart Agent: Fetching logs with filter: {filter_str}")
                print(f"🧠 Smart Agent: Request body: {body}")
                
                resp = requests.post(url, headers=headers, json=body, timeout=60)
                print(f"🧠 Smart Agent: Response status: {resp.status_code}")
                
                if not resp.ok:
                    try:
                        detail = resp.json()
                    except Exception:
                        detail = resp.text
                    print(f"❌ Smart Agent: GCP API error response: {detail}")
                    raise Exception(f"GCP API error {resp.status_code}: {str(detail)}")
                
                data = resp.json() or {}
                entries = data.get("entries", [])
                print(f"🧠 Smart Agent: Received {len(entries)} entries from GCP API")
                
                logs = []
                for idx, entry in enumerate(entries):
                    # Parse entry (exact same format as logs.py route)
                    timestamp = entry.get("timestamp")
                    severity = entry.get("severity", "DEFAULT")
                    json_payload = entry.get("jsonPayload")
                    text_payload = entry.get("textPayload")
                    message = None
                    
                    if isinstance(json_payload, dict):
                        message = json_payload.get("message") or str(json_payload)
                    elif isinstance(text_payload, str):
                        message = text_payload
                    else:
                        message = str(json_payload or text_payload or "")
                    
                    resource = entry.get("resource") or {}
                    resource_type = resource.get("type", "") if isinstance(resource, dict) else ""
                    resource_labels = resource.get("labels", {}) if isinstance(resource, dict) else {}
                    
                    logs.append({
                        "id": entry.get("insertId") or f"entry_{idx}",
                        "timestamp": timestamp,
                        "severity": str(severity),
                        "message": message,
                        "resource": {
                            "type": resource_type,
                            "labels": dict(resource_labels) if isinstance(resource_labels, dict) else {},
                        },
                        "labels": dict(entry.get("labels", {})) if isinstance(entry.get("labels"), dict) else {},
                        "jsonPayload": json_payload if isinstance(json_payload, dict) else None,
                        "textPayload": text_payload if isinstance(text_payload, str) else None,
                        "httpRequest": entry.get("httpRequest"),
                        "traceId": entry.get("trace"),
                        "spanId": entry.get("spanId"),
                        "logName": entry.get("logName"),
                        "projectId": project_id,
                        "insertId": entry.get("insertId"),
                    })
                
                print(f"🧠 Smart Agent: Successfully fetched {len(logs)} logs from GCP")
                return logs
                
            except Exception as e:
                print(f"❌ Smart Agent: Error in fetch_logs_sync: {str(e)}")
                raise e
        
        try:
            # Run the synchronous GCP call in a thread pool to avoid blocking
            with ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor, fetch_logs_sync
                )
            return result
            
        except Exception as e:
            print(f"❌ Smart Agent: Error fetching logs from GCP: {str(e)}")
            # Return empty list instead of raising to allow agent to continue
            return []
    
    async def _log_analysis_node(self, state: AgentState) -> AgentState:
        """Perform AI-powered log analysis."""
        print(f"🧠 Smart Agent: Log analysis node")
        
        try:
            # Check if we have logs to analyze
            if not state.get("relevant_logs"):
                state["analysis"] = "No logs available for analysis."
                state["current_step"] = InvestigationStep.LOG_ANALYSIS
                print(f"🧠 Smart Agent: No logs to analyze")
                return state
            
            print(f"🧠 Smart Agent: Analyzing {len(state['relevant_logs'])} logs")
            
            # Build intelligent analysis prompt
            prompt = self._build_intelligent_analysis_prompt(state)
            
            # Get analysis from Gemini model
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            analysis = response.text or ""
            
            state["analysis"] = analysis
            state["current_step"] = InvestigationStep.LOG_ANALYSIS
            
            print(f"🧠 Smart Agent: Analysis completed")
            
        except Exception as e:
            state["error"] = f"Error in log analysis: {str(e)}"
            print(f"❌ Smart Agent: Log analysis error: {str(e)}")
            import traceback
            print(f"❌ Smart Agent: Traceback: {traceback.format_exc()}")
        
        return state
    
    async def _smart_clarification_node(self, state: AgentState) -> AgentState:
        """Generate smart, contextual clarifying questions."""
        print(f"🧠 Smart Agent: Smart clarification node")
        
        try:
            context = state["investigation_context"]
            missing = context.get("missing", [])
            
            # Generate contextual questions based on what we already know
            clarifying_questions = self._generate_smart_clarifying_questions(context, missing)
            
            state["clarifying_questions"] = clarifying_questions
            state["analysis"] = self._format_smart_clarifying_response(context, clarifying_questions)
            state["current_step"] = InvestigationStep.SMART_CLARIFICATION
            
            print(f"🧠 Smart Agent: Generated {len(clarifying_questions)} smart clarifying questions")
            
        except Exception as e:
            state["error"] = f"Error generating clarification: {str(e)}"
            print(f"❌ Smart Agent: Clarification error: {str(e)}")
        
        return state
    
    def _generate_smart_clarifying_questions(self, context: Dict[str, Any], missing: List[str]) -> List[Dict[str, str]]:
        """Generate smart, contextual clarifying questions."""
        questions = []
        
        # Show what we already know
        known_info = []
        if context.get("services"):
            known_info.append(f"Services: {', '.join(context['services'])}")
        if context.get("time_range"):
            known_info.append(f"Time: {context['time_range'].get('description', 'specified')}")
        if context.get("severity"):
            known_info.append(f"Severity: {', '.join(context['severity'])}")
        
        # Generate contextual questions
        if "services" in missing:
            questions.append({
                "type": "services",
                "question": "Which specific services should I check?",
                "context": f"I know you want to look at {', '.join(known_info) if known_info else 'logs'}, but I need to know which services to focus on.",
                "examples": ["cloud_run_revision", "gce_instance", "cloud_function"]
            })
        
        if "time_range" in missing:
            questions.append({
                "type": "time_range",
                "question": "What time period should I investigate?",
                "context": f"I'm ready to analyze {', '.join(known_info) if known_info else 'the logs'}, but I need a time range.",
                "examples": ["last hour", "last 24 hours", "this week", "yesterday"]
            })
        
        if "severity" in missing:
            questions.append({
                "type": "severity",
                "question": "What severity levels are you interested in?",
                "context": f"I'll check {', '.join(known_info) if known_info else 'the logs'} for you, but I need to know what to look for.",
                "examples": ["ERROR only", "WARNING and ERROR", "all severities"]
            })
        
        return questions
    
    def _format_smart_clarifying_response(self, context: Dict[str, Any], questions: List[Dict[str, str]]) -> str:
        """Format a smart, contextual clarification response."""
        
        # Show what we already know
        known_info = []
        if context.get("services"):
            known_info.append(f"✅ Services: {', '.join(context['services'])}")
        if context.get("time_range"):
            known_info.append(f"✅ Time: {context['time_range'].get('description', 'specified')}")
        if context.get("severity"):
            known_info.append(f"✅ Severity: {', '.join(context['severity'])}")
        
        response_parts = ["I'm almost ready to help you! Here's what I understand so far:"]
        
        if known_info:
            response_parts.append("")
            response_parts.extend(known_info)
        
        response_parts.append("")
        response_parts.append("I just need a few more details to get started:")
        
        for q in questions:
            response_parts.append(f"\n• {q['question']}")
            if q.get('context'):
                response_parts.append(f"  {q['context']}")
            if q.get('examples'):
                response_parts.append(f"  Examples: {', '.join(q['examples'])}")
        
        response_parts.append("\nOnce you provide these details, I'll immediately start analyzing your logs!")
        
        return "\n".join(response_parts)
    
    async def _action_generation_node(self, state: AgentState) -> AgentState:
        """Generate suggested actions based on analysis results."""
        print(f"🧠 Smart Agent: Action generation node")
        
        try:
            actions = self._generate_intelligent_actions(state["investigation_context"], state["relevant_logs"])
            state["actions"] = actions
            state["current_step"] = InvestigationStep.ACTION_GENERATION
            
            print(f"🧠 Smart Agent: Generated {len(actions)} intelligent actions")
            
        except Exception as e:
            state["error"] = f"Error generating actions: {str(e)}"
            print(f"❌ Smart Agent: Action generation error: {str(e)}")
        
        return state
    
    def _generate_intelligent_actions(self, context: Dict[str, Any], logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate intelligent, contextual actions."""
        actions = []
        
        if logs:
            actions.append({
                "label": f"View {len(logs)} relevant logs",
                "actionId": "view_logs",
                "params": {"logCount": len(logs)}
            })
        
        # Context-aware actions
        if context.get("analysis_focus") == "error patterns":
            actions.append({
                "label": "Investigate error patterns",
                "actionId": "investigate_errors",
                "params": {"focus": "errors"}
            })
        
        if context.get("analysis_focus") == "performance issues":
            actions.append({
                "label": "Analyze performance metrics",
                "actionId": "analyze_performance",
                "params": {"focus": "performance"}
            })
        
        # Smart follow-up actions
        if context.get("services") and len(context["services"]) > 1:
            actions.append({
                "label": "Compare across services",
                "actionId": "compare_services",
                "params": {"services": context["services"]}
            })
        
        actions.append({
            "label": "Refine search parameters",
            "actionId": "refine_search",
            "params": {"currentResults": len(logs)}
        })
        
        return actions
    
    async def _complete_node(self, state: AgentState) -> AgentState:
        """Complete the workflow and update conversation context."""
        print(f"🧠 Smart Agent: Complete node")
        
        try:
            if state["session_id"]:
                # Update conversation context with what we learned
                self._update_conversation_context(state)
                
                # Add messages to conversation
                conversation_manager.add_message(
                    state["session_id"],
                    "user",
                    state["question"],
                    metadata={
                        "project_id": state["project_id"],
                        "services": state["investigation_context"].get("services"),
                        "time_range": state["investigation_context"].get("time_range"),
                        "severity": state["investigation_context"].get("severity")
                    }
                )
                
                conversation_manager.add_message(
                    state["session_id"],
                    "assistant",
                    state["analysis"],
                    metadata={
                        "current_step": state["current_step"],
                        "needs_clarification": state["needs_clarification"],
                        "relevant_logs_count": len(state["relevant_logs"])
                    }
                )
            
            state["current_step"] = InvestigationStep.COMPLETE
            state["context_summary"] = self._build_intelligent_context_summary(state)
            
            print(f"🧠 Smart Agent: Workflow completed successfully")
            
        except Exception as e:
            state["error"] = f"Error completing workflow: {str(e)}"
            print(f"❌ Smart Agent: Completion error: {str(e)}")
        
        return state
    
    def _update_conversation_context(self, state: AgentState):
        """Update conversation context with new insights."""
        if not state["session_id"]:
            return
        
        context = state["investigation_context"]
        context_updates = {
            "last_question": state["question"],
            "last_analysis": state["analysis"][:200] + "..." if len(state["analysis"]) > 200 else state["analysis"],
            "current_step": state["current_step"],
            "needs_clarification": state["needs_clarification"],
            "missing_info": state["missing_info"],
            "total_logs_analyzed": len(state["relevant_logs"]),
            "investigation_path": [f"Completed {state['current_step']} step"]
        }
        
        # Update with what we learned
        if context.get("services"):
            context_updates["services"] = context["services"]
        if context.get("time_range"):
            context_updates["time_range"] = context["time_range"]
        if context.get("severity"):
            context_updates["severity_filters"] = context["severity"]
        
        conversation_manager.update_context(state["session_id"], context_updates)
    
    def _build_intelligent_context_summary(self, state: AgentState) -> str:
        """Build an intelligent summary of the current context."""
        if not state["session_id"]:
            return "Starting fresh investigation"
        
        session = conversation_manager.get_session(state["session_id"])
        if not session:
            return "Session not found"
        
        context = session.context
        summary_parts = []
        
        if context.get("last_question"):
            summary_parts.append(f"Last question: {context['last_question'][:100]}...")
        
        if context.get("services"):
            summary_parts.append(f"Focusing on: {', '.join(context['services'])}")
        
        if context.get("time_range"):
            summary_parts.append(f"Time range: {context['time_range'].get('description', 'specified')}")
        
        if context.get("severity_filters"):
            summary_parts.append(f"Severity: {', '.join(context['severity_filters'])}")
        
        if context.get("total_logs_analyzed"):
            summary_parts.append(f"Logs analyzed: {context['total_logs_analyzed']}")
        
        return "; ".join(summary_parts) if summary_parts else "No specific context set"
    
    def _build_intelligent_analysis_prompt(self, state: AgentState) -> str:
        """Build an intelligent analysis prompt."""
        
        context = state["investigation_context"]
        
        # Format logs for context
        context_lines = []
        for log in state["relevant_logs"][:state["limit"]]:
            if not log or not isinstance(log, dict):
                continue
                
            ts = log.get("timestamp") or log.get("time")
            sev = log.get("severity")
            msg = log.get("message") or log.get("textPayload")
            svc = (log.get("resource") or {}).get("type") if isinstance(log.get("resource"), dict) else None
            insert_id = log.get("id") or log.get("insertId")
            context_lines.append(f"[{ts}] [{sev}] [{svc}] ({insert_id}) {str(msg)[:500]}")
        
        context_text = "\n".join(context_lines)
        
        # Build conversation history
        conversation_history = ""
        if state["session_id"]:
            session = conversation_manager.get_session(state["session_id"])
            if session and session.messages:
                conversation_history = "\n".join([
                    f"{msg.role.upper()}: {msg.content}" for msg in session.messages[-5:]
                ])
        
        # Create intelligent prompt
        time_range_desc = "Not specified"
        if context.get("time_range") and isinstance(context["time_range"], dict):
            time_range_desc = context["time_range"].get("description", "Not specified")
        
        # Safe list handling for join operations
        services_list = context.get("services") or []
        severity_list = context.get("severity") or []
        
        services_str = ', '.join(services_list) if services_list else "Not specified"
        severity_str = ', '.join(severity_list) if severity_list else "All levels"
        
        prompt = f"""You are a senior SRE conducting an intelligent log investigation. Analyze the provided logs and provide actionable insights.

INVESTIGATION CONTEXT:
- Project ID: {state["project_id"]}
- Services: {services_str}
- Time Range: {time_range_desc}
- Severity Focus: {severity_str}
- Search Query: {context.get("search_query", state["question"])}

CONVERSATION HISTORY:
{conversation_history or "This is the start of our investigation."}

RELEVANT LOGS ({len(state["relevant_logs"])} logs):
{context_text}

USER QUESTION: {state["question"]}

INSTRUCTIONS:
1. Analyze the logs for patterns, errors, and insights based on the user's focus
2. Provide specific evidence from the logs (cite insertId when possible)
3. Consider the conversation context and build upon previous insights
4. Suggest next investigation steps that would be most valuable
5. Be conversational but professional - you're an SRE partner
6. Focus on actionable insights that help resolve the user's concern

Please analyze these logs and provide a comprehensive answer to: {state["question"]}"""
        
        return prompt
    
    def _format_logs_for_ui(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format logs for UI display."""
        formatted_logs = []
        for log in logs:
            if not log or not isinstance(log, dict):
                continue
                
            formatted_logs.append({
                "id": str(log.get("id") or log.get("insertId") or "unknown"),
                "insertId": log.get("insertId"),
                "timestamp": log.get("timestamp"),
                "severity": log.get("severity"),
                "messageSnippet": (log.get("message") or log.get("textPayload") or "")[:250],
                "serviceId": (log.get("resource") or {}).get("type") if isinstance(log.get("resource"), dict) else None,
                "traceId": log.get("traceId") or log.get("trace"),
                "score": log.get("_score", 0.0),
                "raw": log,
            })
        return formatted_logs
    
    def _format_response(self, state: AgentState) -> Dict[str, Any]:
        """Format the final response for the API."""
        return {
            "analysis": state["analysis"],
            "toolResults": state["tool_results"],
            "sessionId": state["session_id"],
            "contextSummary": state["context_summary"],
            "actions": state["actions"],
            "needsClarification": state["needs_clarification"],
            "missingInfo": state["missing_info"],
            "relevantLogs": state["relevant_logs"],
            "clarifyingQuestions": state["clarifying_questions"],
            "currentStep": state["current_step"],
            "error": state["error"]
        }
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        messages = conversation_manager.get_conversation_history(session_id, limit)
        return [msg.to_dict() for msg in messages]

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        return conversation_manager.get_user_sessions(user_id)


# Alias for backward compatibility
LangGraphAgent = SmartLangGraphAgent
