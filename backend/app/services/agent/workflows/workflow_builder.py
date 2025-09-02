"""
Workflow Builder

Builds and manages the LangGraph workflow for the intelligent agent.
Handles node creation, edge definition, and workflow orchestration.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any

from ..core.state import AgentState, InvestigationStep


class WorkflowBuilder:
    """Builder for the LangGraph agent workflow."""
    
    def __init__(self, agent_instance):
        self.agent = agent_instance
    
    def build_workflow(self) -> StateGraph:
        """Build the complete intelligent workflow graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        self._add_nodes(workflow)
        
        # Define edges
        self._add_edges(workflow)
        
        # Set entry point
        workflow.set_entry_point("intelligent_analysis")
        
        return workflow.compile()
    
    def _add_nodes(self, workflow: StateGraph):
        """Add all workflow nodes."""
        workflow.add_node("intelligent_analysis", self.agent._intelligent_analysis_node)
        workflow.add_node("context_retrieval", self.agent._context_retrieval_node)
        workflow.add_node("log_analysis", self.agent._log_analysis_node)
        workflow.add_node("smart_clarification", self.agent._smart_clarification_node)
        workflow.add_node("action_generation", self.agent._action_generation_node)
        workflow.add_node("complete", self.agent._complete_node)
    
    def _add_edges(self, workflow: StateGraph):
        """Add workflow edges and conditional routing."""
        # Add conditional edges with smart routing
        workflow.add_conditional_edges(
            "intelligent_analysis",
            self.agent._smart_decision_router,
            {
                "proceed_with_analysis": "context_retrieval",
                "need_minimal_clarification": "smart_clarification",
                "proceed_with_partial": "context_retrieval"
            }
        )
        
        # Add linear edges
        workflow.add_edge("context_retrieval", "log_analysis")
        workflow.add_edge("log_analysis", "action_generation")
        workflow.add_edge("action_generation", "complete")
        workflow.add_edge("smart_clarification", "complete")
