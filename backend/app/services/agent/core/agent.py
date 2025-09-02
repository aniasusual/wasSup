"""
Smart LangGraph Agent Core

The main agent class that orchestrates the intelligent log analysis workflow.
Handles conversation management, context building, and AI-powered analysis.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .state import AgentState, InvestigationStep, LogEntry
from ..parsers.text_parser import RobustTextParser
from ..integrations.gcp_client import GCPLoggingClient
from ..integrations.resource_discovery import GCPResourceDiscovery
from ..workflows.workflow_builder import WorkflowBuilder
from ...conversation_manager import conversation_manager

logger = logging.getLogger(__name__)


class SmartLangGraphAgent:
    """
    Intelligent LangGraph-based agent that can handle partial information,
    build context incrementally, and make smart decisions about when to proceed.
    """
    
    def __init__(self):
        self._initialize_gemini()
        self._initialize_components()
        self._build_workflow()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI model."""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
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
    
    def _initialize_components(self):
        """Initialize agent components."""
        self.robust_parser = RobustTextParser()
        self.gcp_logging_client = GCPLoggingClient()
        self.gcp_resource_discovery = GCPResourceDiscovery()
    
    def _build_workflow(self):
        """Build the intelligent workflow graph."""
        workflow_builder = WorkflowBuilder(self)
        self.workflow = workflow_builder.build_workflow()
    
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
        
        Args:
            question: User's question or query
            project_id: GCP project ID
            session_id: Optional session ID for conversation continuity
            user_id: Optional user ID
            services: Optional list of services to focus on
            time_range: Optional time range for analysis
            collection: Optional collection name
            limit: Maximum number of logs to analyze
            access_token: OAuth2 access token for GCP API
            
        Returns:
            Analysis results and recommendations
        """
        logger.info(f"🧠 Smart LangGraph Agent: Starting intelligent analysis for project_id={project_id}")
        
        # Initialize state with conversation context
        initial_state = self._create_initial_state(
            question, project_id, session_id, user_id, services, 
            time_range, collection, limit, access_token
        )
        
        # Handle session management
        self._handle_session_management(initial_state, user_id, project_id, question)
        
        # Load existing conversation context
        self._load_conversation_context(initial_state)
        
        # Run the intelligent workflow
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("🧠 Smart LangGraph Agent: Workflow completed successfully")
            
            return self._format_response(final_state)
            
        except Exception as e:
            error_msg = f"Error in intelligent LangGraph workflow: {str(e)}"
            logger.error(f"❌ Smart LangGraph Agent: Error: {error_msg}")
            
            return {
                "analysis": error_msg,
                "toolResults": None,
                "sessionId": session_id,
                "contextSummary": "Error occurred during analysis",
                "actions": [],
                "needsClarification": False,
                "error": str(e)
            }
    
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
        
        Yields:
            Progress updates in SSE format
        """
        # Yield initial status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting intelligent analysis...', 'step': 'initialization'})}\n\n"
        
        logger.info(f"🧠 Smart LangGraph Agent: Starting streaming analysis for project_id={project_id}")
        
        # Initialize state
        initial_state = self._create_initial_state(
            question, project_id, session_id, user_id, services, 
            time_range, collection, limit, access_token
        )
        
        # Handle session management
        self._handle_session_management(initial_state, user_id, project_id, question)
        
        # Load conversation context
        self._load_conversation_context(initial_state)
        
        # Run workflow with streaming updates
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Running intelligent workflow...', 'step': 'workflow_start'})}\n\n"
            
            final_state = initial_state
            async for update in self._run_workflow_streaming(initial_state, yield_updates=True):
                yield update
                # Check if this is the final state update
                if update.startswith("data: "):
                    try:
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
            logger.error(f"❌ Smart LangGraph Agent: Error: {error_msg}")
            
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
    
    def _create_initial_state(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str],
        user_id: Optional[str],
        services: Optional[List[str]],
        time_range: Optional[Dict[str, str]],
        collection: Optional[str],
        limit: int,
        access_token: Optional[str]
    ) -> AgentState:
        """Create initial agent state."""
        return AgentState(
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
    
    def _handle_session_management(self, state: AgentState, user_id: Optional[str], project_id: str, question: str):
        """Handle session creation and management."""
        if not state["session_id"] and user_id:
            state["session_id"] = conversation_manager.create_session(
                user_id=user_id,
                project_id=project_id,
                initial_context={
                    "project_id": project_id,
                    "last_question": question,
                    "analysis_history": []
                }
            )
    
    def _load_conversation_context(self, state: AgentState):
        """Load existing conversation context if available."""
        if state["session_id"]:
            session = conversation_manager.get_session(state["session_id"])
            if session:
                state["conversation_context"] = self._extract_conversation_context(session)
    
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
    
    async def _run_workflow_streaming(self, initial_state: AgentState, yield_updates: bool = False):
        """
        Run the workflow with streaming updates.
        
        Yields:
            Progress updates in SSE format
        """
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
    
    # Node implementations (to be moved to separate files)
    async def _intelligent_analysis_node(self, state: AgentState) -> AgentState:
        """Intelligently analyze user input and conversation context."""
        logger.info("🧠 Smart Agent: Intelligent analysis node")
        
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
        
        logger.info(f"🧠 Smart Agent: Parsed info: {parsed_info}")
        logger.info(f"🧠 Smart Agent: Missing info: {state['missing_info']}")
        
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
        
        # Determine what's missing - only time_range is required
        missing = []
        confidence_threshold = 0.7
        
        # Only time_range is required - services, severity, and search are optional
        if not time_range or (extracted_time_range and extracted_time_range.get("confidence", 0) < confidence_threshold):
            missing.append("time_range")
        
        # Services are optional - user can choose to analyze all services or specific ones
        if not services or (extracted_services and extracted_services[0]["confidence"] < confidence_threshold):
            missing.append("services")
        
        # Severity is optional - user can choose to filter by severity or not
        if not severity or (extracted_severities and extracted_severities[0]["confidence"] < confidence_threshold):
            missing.append("severity")
        
        # Check if we have enough context to proceed
        # Only time_range is required - everything else is optional
        has_minimal_context = time_range is not None
        has_required_context = time_range is not None
        
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
            "has_required_context": has_required_context,
            "can_proceed": has_required_context,  # Only proceed if time_range is available
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
        
        # Re-evaluate what's missing - only time_range is required
        missing = []
        if not merged["services"]:
            missing.append("services")
        if not merged["time_range"]:
            missing.append("time_range")
        if not merged["severity"]:
            missing.append("severity")
        
        merged["missing"] = missing
        
        # Only time_range is required - services and severity are optional
        time_range_exists = merged["time_range"] is not None
        
        merged["has_minimal_context"] = time_range_exists
        merged["has_required_context"] = time_range_exists
        merged["can_proceed"] = time_range_exists  # Only proceed if time_range is available
        
        return merged
    
    def _smart_decision_router(self, state: AgentState) -> str:
        """Make intelligent decisions about workflow routing."""
        context = state["investigation_context"]
        
        if context.get("can_proceed", False):
            # If we have the required time_range, proceed with analysis
            # All other filters (services, severity, search) are optional
            return "proceed_with_analysis"
        else:
            # Only ask for clarification if time_range is missing
            return "need_minimal_clarification"
    
    # Node implementations using the modular components
    async def _context_retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant context and logs using GCP Logging API with fallback strategies."""
        from ..nodes.context_retrieval import ContextRetrievalNode
        
        context_retrieval = ContextRetrievalNode(self.gcp_logging_client, self.gcp_resource_discovery)
        return await context_retrieval.execute(state)
    
    async def _context_retrieval_node_streaming(self, state: AgentState, yield_updates: bool = False):
        """Retrieve relevant context and logs using GCP Logging API with streaming updates."""
        from ..nodes.context_retrieval import ContextRetrievalNode
        
        context_retrieval = ContextRetrievalNode(self.gcp_logging_client, self.gcp_resource_discovery)
        async for update in context_retrieval.execute_streaming(state, yield_updates):
            yield update
    
    async def _log_analysis_node(self, state: AgentState) -> AgentState:
        """Perform AI-powered log analysis."""
        from ..nodes.log_analysis import LogAnalysisNode
        
        log_analysis = LogAnalysisNode(self.model)
        return await log_analysis.execute(state)
    
    async def _smart_clarification_node(self, state: AgentState) -> AgentState:
        """Generate smart, contextual clarifying questions."""
        logger.info("🧠 Smart Agent: Smart clarification node")
        
        try:
            context = state["investigation_context"]
            missing = context.get("missing", [])
            
            # Generate contextual questions based on what we already know
            clarifying_questions = self._generate_smart_clarifying_questions(context, missing)
            
            state["clarifying_questions"] = clarifying_questions
            state["analysis"] = self._format_smart_clarifying_response(context, clarifying_questions)
            state["current_step"] = InvestigationStep.SMART_CLARIFICATION
            
            logger.info(f"🧠 Smart Agent: Generated {len(clarifying_questions)} smart clarifying questions")
            
        except Exception as e:
            state["error"] = f"Error generating clarification: {str(e)}"
            logger.error(f"❌ Smart Agent: Clarification error: {str(e)}")
        
        return state
    
    async def _action_generation_node(self, state: AgentState) -> AgentState:
        """Generate suggested actions based on analysis results."""
        logger.info("🧠 Smart Agent: Action generation node")
        
        try:
            actions = self._generate_intelligent_actions(state["investigation_context"], state["relevant_logs"])
            state["actions"] = actions
            state["current_step"] = InvestigationStep.ACTION_GENERATION
            
            logger.info(f"🧠 Smart Agent: Generated {len(actions)} intelligent actions")
            
        except Exception as e:
            state["error"] = f"Error generating actions: {str(e)}"
            logger.error(f"❌ Smart Agent: Action generation error: {str(e)}")
        
        return state
    
    async def _complete_node(self, state: AgentState) -> AgentState:
        """Complete the workflow and update conversation context."""
        logger.info("🧠 Smart Agent: Complete node")
        
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
            
            logger.info("🧠 Smart Agent: Workflow completed successfully")
            
        except Exception as e:
            state["error"] = f"Error completing workflow: {str(e)}"
            logger.error(f"❌ Smart Agent: Completion error: {str(e)}")
        
        return state
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        messages = conversation_manager.get_conversation_history(session_id, limit)
        return [msg.to_dict() for msg in messages]

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        return conversation_manager.get_user_sessions(user_id)
    
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
        
        # Generate contextual questions - only time_range is required
        if "time_range" in missing:
            questions.append({
                "type": "time_range",
                "question": "What time period should I investigate?",
                "context": f"I'm ready to analyze your logs, but I need to know the time period to focus on.",
                "examples": ["last hour", "last 24 hours", "this week", "yesterday", "last 30 minutes"]
            })
        
        # Services are optional - only ask if user seems to want specific services
        if "services" in missing and context.get("time_range"):
            # Only ask about services if we have time_range and user might want specific services
            questions.append({
                "type": "services",
                "question": "Would you like me to focus on specific services, or analyze across ALL services?",
                "context": f"I can analyze logs across all services in your project, or focus on specific ones if you prefer.",
                "examples": ["all services", "cloud_run_revision", "gce_instance", "cloud_function", "across all services"]
            })
        
        # Severity is optional - only ask if user seems to want severity filtering
        if "severity" in missing and context.get("time_range"):
            # Only ask about severity if we have time_range and user might want severity filtering
            questions.append({
                "type": "severity",
                "question": "Would you like me to filter by specific severity levels, or show all log levels?",
                "context": f"I can show all log levels, or focus on specific severities like errors or warnings.",
                "examples": ["all severities", "ERROR only", "WARNING and ERROR", "just errors"]
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
        
        response_parts = ["I'm ready to help you analyze your logs! Here's what I understand so far:"]
        
        if known_info:
            response_parts.append("")
            response_parts.extend(known_info)
        
        response_parts.append("")
        
        # Check if time_range is missing (the only required field)
        time_missing = any(q["type"] == "time_range" for q in questions)
        
        if time_missing:
            response_parts.append("I just need to know the time period to analyze:")
        else:
            response_parts.append("I have everything I need to get started! Here are some optional filters you can specify:")
        
        for q in questions:
            if q["type"] == "time_range":
                response_parts.append(f"\n• {q['question']}")
                if q.get('context'):
                    response_parts.append(f"  {q['context']}")
                if q.get('examples'):
                    response_parts.append(f"  Examples: {', '.join(q['examples'])}")
            else:
                # Optional filters
                response_parts.append(f"\n• {q['question']} (optional)")
                if q.get('context'):
                    response_parts.append(f"  {q['context']}")
                if q.get('examples'):
                    response_parts.append(f"  Examples: {', '.join(q['examples'])}")
        
        if time_missing:
            response_parts.append("\nOnce you provide the time period, I'll immediately start analyzing your logs!")
        else:
            response_parts.append("\nI can start analyzing now, or you can specify additional filters if you'd like!")
        
        return "\n".join(response_parts)
    
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
