"""
Main LangGraph workflow implementation.

This module contains the core StateGraph workflow for the
GCP Log Investigation Agent.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
# Note: Using in-memory checkpointing for now - will implement persistent storage later

try:
    # Try relative imports first (for normal usage)
    from ....models.agent import AgentState, WorkflowConfig, NodeResult
    from .graph_nodes.user_query_input_node import UserQueryInputNode
    from .graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
    from .graph_nodes.session_complete_node import SessionCompleteNode
    from .architecture_loader_node import ArchitectureLoaderNode
except ImportError:
    # Fall back to absolute imports (for LangGraph Studio)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from app.models.agent import AgentState, WorkflowConfig, NodeResult
    from app.services.agent.core.graph_nodes.user_query_input_node import UserQueryInputNode
    from app.services.agent.core.graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
    from app.services.agent.core.graph_nodes.session_complete_node import SessionCompleteNode
    from app.services.agent.core.architecture_loader_node import ArchitectureLoaderNode

logger = logging.getLogger(__name__)


class GCPLogInvestigationAgent:
    """
    Main agent class that orchestrates the LangGraph workflow.
    
    This class manages the complete investigation workflow from user input
    to final analysis results using a state-driven graph approach.
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Workflow configuration settings
        """
        
        self.config = config or WorkflowConfig()
        self.graph = None
        # Note: Using in-memory checkpointing for now - will implement persistent storage later
        
        self._build_workflow()
        
        logger.info(f"GCPLogInvestigationAgent initialized with config: {self.config}")
    
    def _build_workflow(self) -> None:
        """
        Build the LangGraph StateGraph workflow.
        
        This method constructs the complete workflow graph with all nodes
        and conditional edges according to the investigation flow.
        """
        
        # Create the StateGraph
        workflow = StateGraph(AgentState)
        
        # Initialize node instances
        user_query_node = UserQueryInputNode(self.config)
        architecture_loader_node = ArchitectureLoaderNode(self.config)
        intent_analysis_node = IntentAndQueryAnalysisNode(self.config)
        session_complete_node = SessionCompleteNode(self.config)
        
        # Add nodes to the workflow
        workflow.add_node("user_query_input", user_query_node.execute)
        workflow.add_node("architecture_loader", architecture_loader_node.execute)
        workflow.add_node("intent_and_query_analysis", intent_analysis_node.execute)
        workflow.add_node("session_complete", session_complete_node.execute)
        
        # TODO: Add more nodes as we implement them
        # workflow.add_node("intent_classification", intent_classification_node.execute)
        # workflow.add_node("architecture_loader", architecture_loader_node.execute)
        # workflow.add_node("filter_construction", filter_construction_node.execute)
        # workflow.add_node("api_orchestrator", api_orchestrator_node.execute)
        # workflow.add_node("log_analysis", log_analysis_node.execute)
        # workflow.add_node("correlation_engine", correlation_engine_node.execute)
        # workflow.add_node("synthesis_engine", synthesis_engine_node.execute)
        # workflow.add_node("context_manager", context_manager_node.execute)
        
        # Set entry point
        workflow.set_entry_point("user_query_input")
        
        # Add edges for Phase 1 flow: A -> A1 -> (B + C combined) -> END
        workflow.add_edge("user_query_input", "architecture_loader")
        workflow.add_edge("architecture_loader", "intent_and_query_analysis")
        
        # Route to session completion for Phase 1
        workflow.add_conditional_edges(
            "intent_and_query_analysis",
            self._route_after_intent_analysis,
            {
                "proceed": "session_complete",
                "needs_clarification": "session_complete",
            }
        )
        workflow.add_edge("session_complete", END)
        
        # TODO: Add conditional edges for routing decisions as we add more nodes
        # workflow.add_conditional_edges(
        #     "user_query_input",
        #     self._route_after_input_analysis,
        #     {
        #         "needs_clarification": "clarification",
        #         "proceed": "architecture_loader"
        #     }
        # )
        
        # Compile the workflow
        self.graph = workflow.compile()
        
        logger.info("LangGraph workflow built successfully")
    
    def get_graph(self):
        """
        Get the compiled LangGraph for LangGraph Studio.
        
        Returns:
            Compiled LangGraph workflow
        """
        if not self.graph:
            self._build_workflow()
        return self.graph
    
    def _route_after_input_analysis(self, state: AgentState) -> str:
        """
        Route decision after input analysis node.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to execute
        """
        
        if state.get("needs_clarification", False):
            return "clarification"
        return "intent_classification"

    def _route_after_intent_analysis(self, state: AgentState) -> str:
        """Route decision after intent + query analysis.
        Returns one of: 'needs_clarification', 'proceed'."""
        if state.get("needs_clarification", False):
            return "needs_clarification"
        return "proceed"
    
    async def process_query(
        self,
        query_input: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete workflow.
        
        Args:
            query_input: User query input data
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Complete analysis results
        """
        try:
            
            logger.info(f"Processing query: {query_input.get('question', 'Unknown')}")
            
            # Initialize state from input
            initial_state = self._create_initial_state(query_input, session_id)
            
            # Execute the workflow
            config = {"configurable": {"thread_id": session_id or "default"}}
            
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            
            # Format response
            response = self._format_response(final_state)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return self._format_error_response(str(e))
    
    async def process_query_stream(
        self,
        query_input: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """
        Process a user query with streaming responses.
        
        Args:
            query_input: User query input data
            session_id: Optional session ID for conversation continuity
            
        Yields:
            Streaming chunks of analysis results
        """
        try:
            logger.info(f"Processing streaming query: {query_input.get('question', 'Unknown')}")

            # Initialize state from input
            state = self._create_initial_state(query_input, session_id)

            # Instantiate nodes explicitly to step through for streaming updates
            try:
                # Local imports to avoid circulars
                from .graph_nodes.user_query_input_node import UserQueryInputNode
                from .architecture_loader_node import ArchitectureLoaderNode
                from .graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
                from .graph_nodes.session_complete_node import SessionCompleteNode
            except Exception:
                # Fallback absolute imports
                from app.services.agent.core.graph_nodes.user_query_input_node import UserQueryInputNode
                from app.services.agent.core.architecture_loader_node import ArchitectureLoaderNode
                from app.services.agent.core.graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
                from app.services.agent.core.graph_nodes.session_complete_node import SessionCompleteNode

            user_query_node = UserQueryInputNode(self.config)
            architecture_loader_node = ArchitectureLoaderNode(self.config)
            intent_node = IntentAndQueryAnalysisNode(self.config)
            session_node = SessionCompleteNode(self.config)

            # Helper to emit a node event
            async def emit_node_event(node_key: str, title: str, status: str, data: Dict[str, Any]):
                yield {
                    "type": "node_event",
                    "node": node_key,
                    "title": title,
                    "status": status,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # A: User Query Input
            async for evt in emit_node_event("user_query_input", "User Query Input", "started", {
                "question_preview": (state.get("question") or "")[:120],
                "project_id": state.get("project_id")
            }):
                yield evt
            state = await user_query_node.execute(state)
            async for evt in emit_node_event("user_query_input", "User Query Input", "completed", {
                "processed_question": state.get("processed_question"),
            }):
                yield evt

            # A1: Architecture Loader
            async for evt in emit_node_event("architecture_loader", "Load Project Architecture", "started", {
                "project_id": state.get("project_id")
            }):
                yield evt
            state = await architecture_loader_node.execute(state)
            arch_ctx = state.get("architecture_context") or {}
            arch_tool = ((state.get("tool_results") or {}).get("architecture_loader") or {})
            async for evt in emit_node_event("architecture_loader", "Load Project Architecture", "completed", {
                "parsing_method": arch_tool.get("parsing_method"),
                "relevant_services": state.get("relevant_services"),
                "insights": state.get("architecture_insights"),
                "context_summary": arch_ctx.get("context_summary")
            }):
                yield evt

            # B + C: Intent & Query Analysis
            async for evt in emit_node_event("intent_and_query_analysis", "Intent & Query Analysis", "started", {
                "note": "Extracting entities and classifying query"
            }):
                yield evt
            state = await intent_node.execute(state)
            nlp_tool = ((state.get("tool_results") or {}).get("nlp_analysis") or {})
            class_result = nlp_tool.get("classification_result") or {}
            async for evt in emit_node_event("intent_and_query_analysis", "Intent & Query Analysis", "completed", {
                "query_type": state.get("query_type"),
                "needs_clarification": state.get("needs_clarification"),
                "missing_info": state.get("missing_info"),
                "extracted_entities": state.get("extracted_entities"),
                "classification": class_result
            }):
                yield evt
            # UU: Session Complete
            async for evt in emit_node_event("session_complete", "Session", "started", {
                "note": "Marking session ready for next query"
            }):
                yield evt
            state = await session_node.execute(state)
            async for evt in emit_node_event("session_complete", "Session", "completed", {
                "session_status": state.get("session_status"),
                "session_ready_at": state.get("session_ready_at"),
                "context_summary": state.get("context_summary"),
            }):
                yield evt

            # Finally, stream the analysis text in chunks for a nicer UX
            analysis = state.get("analysis", "")
            if analysis:
                words = analysis.split()
                chunk_size = 5
                import asyncio
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = " ".join(chunk_words)
                    if i + chunk_size < len(words):
                        chunk_text += " "
                    yield {
                        "type": "chunk",
                        "content": chunk_text
                    }
                    await asyncio.sleep(0.03)

            # Send final result
            response = self._format_response(state)
            yield {
                "type": "result",
                "data": response
            }

            logger.info("Streaming query processing completed successfully")

        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}", exc_info=True)
            yield {"type": "error", "message": str(e)}
    
    def _create_initial_state(self, query_input: Dict[str, Any], session_id: Optional[str]) -> AgentState:
        """
        Create initial agent state from query input.
        
        Args:
            query_input: Raw query input data
            session_id: Optional session ID
            
        Returns:
            Initialized AgentState
        """
        
        investigation_id = f"inv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return AgentState(
            # User inputs
            question=query_input.get("question", ""),
            project_id=query_input.get("project_id", ""),
            session_id=session_id,
            user_id=query_input.get("user_id"),
            services=query_input.get("services"),
            time_range=query_input.get("time_range"),
            collection=query_input.get("collection"),
            limit=query_input.get("limit", 1000),
            access_token=query_input.get("access_token"),
            
            # Agent workflow state
            current_step="user_query_input",
            needs_clarification=False,
            missing_info=[],
            investigation_context={
                "investigation_id": f"inv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "start_time": datetime.utcnow(),
                "current_focus": "",
                "evidence_collected": [],
                "hypotheses": [],
                "confidence_level": 0.0,
                "next_steps": []
            },
            
            # Results and outputs
            analysis="",
            tool_results=None,
            actions=[],
            relevant_logs=[],
            clarifying_questions=[],
            
            # Conversation management
            conversation_history=[],
            context_summary="",
            error=None,
            
            # Query processing state
            query_type=None,
            extracted_entities={},
            processed_question="",
            
            # API interaction state
            api_calls_made=0,
            last_api_call_time=None,
            rate_limit_info=None,
            
            # Learning and memory
            discovered_patterns=[],
            user_preferences={},
            architecture_insights={},
            
            # Architecture context (for A1 node)
            architecture_context=None,
            relevant_services=None
        )
    
    def _format_response(self, final_state: AgentState) -> Dict[str, Any]:
        """
        Format the final state into a response for the API.
        
        Args:
            final_state: Final agent state after workflow execution
            
        Returns:
            Formatted response dictionary
        """
        
        # Check if there was an error during processing
        has_error = final_state.get("error") is not None
        is_error_step = final_state.get("current_step", "").endswith("_error")
        
        
        return {
            "success": not (has_error or is_error_step),
            "analysis": final_state.get("analysis", ""),
            "session_id": final_state.get("session_id"),
            "context_summary": final_state.get("context_summary", ""),
            "actions": final_state.get("actions", []),
            "needs_clarification": final_state.get("needs_clarification", False),
            "missing_info": final_state.get("missing_info", []),
            "relevant_logs": final_state.get("relevant_logs", []),
            "clarifying_questions": final_state.get("clarifying_questions", []),
            "current_step": final_state.get("current_step", "complete"),
            "error": final_state.get("error"),
            "tool_results": final_state.get("tool_results"),
            "metadata": {
                "query_type": final_state.get("query_type"),
                "extracted_entities": final_state.get("extracted_entities", {}),
                "api_calls_made": final_state.get("api_calls_made", 0),
                "execution_time": datetime.utcnow().isoformat()
            }
        }
    
    def _format_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Format an error response.
        
        Args:
            error_message: Error message to include
            
        Returns:
            Formatted error response
        """
        
        return {
            "success": False,
            "analysis": "",
            "session_id": None,
            "context_summary": "",
            "actions": [],
            "needs_clarification": False,
            "missing_info": [],
            "relevant_logs": [],
            "clarifying_questions": [],
            "current_step": "error",
            "error": error_message,
            "tool_results": None,
            "metadata": {
                "execution_time": datetime.utcnow().isoformat()
            }
        }


# Global agent instance for LangGraph Studio
_agent_instance = None

def get_agent_graph():
    """
    Get the compiled LangGraph for LangGraph Studio.
    
    This function is called by LangGraph Studio to get the workflow graph.
    
    Returns:
        Compiled LangGraph workflow
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = GCPLogInvestigationAgent()
    return _agent_instance.get_graph()
