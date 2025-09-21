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
    from .graph_nodes.direct_filter_construction_node import DirectFilterConstructionNode
    from .graph_nodes.single_stage_filter_construction_node import SingleStageFilterConstructionNode
    from .graph_nodes.context_aware_enhancement_node import ContextAwareEnhancementNode
    from .graph_nodes.session_complete_node import SessionCompleteNode
    from .graph_nodes.filter_validation_optimization_node import FilterValidationOptimizationNode
    from .graph_nodes.primary_call_preparation_node import PrimaryCallPreparationNode
    from .graph_nodes.execute_logging_api_node import ExecuteLoggingAPINode
    from .graph_nodes.present_results_node import PresentResultsNode
    from .graph_nodes.response_analysis_node import ResponseAnalysisNode
    from .graph_nodes.multi_dimensional_analysis_node import MultiDimensionalAnalysisNode
    from .graph_nodes.architecture_query_decomposition_node import ArchitectureAwareQueryDecompositionNode
    from .graph_nodes.dependency_strategy_node import DependencyStrategyNode
    from .graph_nodes.context_enhanced_filter_builder_node import ContextEnhancedFilterBuilderNode
    from .graph_nodes.multi_stage_filter_planning_node import MultiStageFilterPlanningNode
    from .graph_nodes.auto_refine_filters_node import AutoRefineFiltersNode
    from .graph_nodes.broaden_search_node import BroadenSearchNode
    from .graph_nodes.arch_resource_discovery_node import ArchResourceDiscoveryNode
    from .graph_nodes.upstream_downstream_check_node import UpstreamDownstreamCheckNode
    from .graph_nodes.response_analysis_node import ResponseAnalysisNode
    from .architecture_loader_node import ArchitectureLoaderNode
    from .graph_nodes.cross_service_correlation_node import CrossServiceCorrelationNode
    from .graph_nodes.automated_followup_investigations_node import AutomatedFollowupInvestigationsNode
    from .graph_nodes.dependency_chain_analysis_node import DependencyChainAnalysisNode
    from .graph_nodes.infrastructure_impact_assessment_node import InfrastructureImpactAssessmentNode
    from .graph_nodes.resource_utilization_correlation_node import ResourceUtilizationCorrelationNode
    from .graph_nodes.evidence_aggregation_node import EvidenceAggregationNode
except ImportError:
    # Fall back to absolute imports (for LangGraph Studio)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from app.models.agent import AgentState, WorkflowConfig, NodeResult
    from app.services.agent.core.graph_nodes.user_query_input_node import UserQueryInputNode
    from app.services.agent.core.graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
    from app.services.agent.core.graph_nodes.direct_filter_construction_node import DirectFilterConstructionNode
    from app.services.agent.core.graph_nodes.single_stage_filter_construction_node import SingleStageFilterConstructionNode
    from app.services.agent.core.graph_nodes.context_aware_enhancement_node import ContextAwareEnhancementNode
    from app.services.agent.core.graph_nodes.session_complete_node import SessionCompleteNode
    from app.services.agent.core.graph_nodes.filter_validation_optimization_node import FilterValidationOptimizationNode
    from app.services.agent.core.graph_nodes.primary_call_preparation_node import PrimaryCallPreparationNode
    from app.services.agent.core.graph_nodes.execute_logging_api_node import ExecuteLoggingAPINode
    from app.services.agent.core.graph_nodes.present_results_node import PresentResultsNode
    from app.services.agent.core.graph_nodes.response_analysis_node import ResponseAnalysisNode
    from app.services.agent.core.graph_nodes.multi_dimensional_analysis_node import MultiDimensionalAnalysisNode
    from app.services.agent.core.graph_nodes.architecture_query_decomposition_node import ArchitectureAwareQueryDecompositionNode
    from app.services.agent.core.graph_nodes.dependency_strategy_node import DependencyStrategyNode
    from app.services.agent.core.graph_nodes.context_enhanced_filter_builder_node import ContextEnhancedFilterBuilderNode
    from app.services.agent.core.graph_nodes.multi_stage_filter_planning_node import MultiStageFilterPlanningNode
    from app.services.agent.core.graph_nodes.auto_refine_filters_node import AutoRefineFiltersNode
    from app.services.agent.core.graph_nodes.broaden_search_node import BroadenSearchNode
    from app.services.agent.core.graph_nodes.arch_resource_discovery_node import ArchResourceDiscoveryNode
    from app.services.agent.core.graph_nodes.upstream_downstream_check_node import UpstreamDownstreamCheckNode
    from app.services.agent.core.graph_nodes.response_analysis_node import ResponseAnalysisNode
    from app.services.agent.core.architecture_loader_node import ArchitectureLoaderNode
    from app.services.agent.core.graph_nodes.cross_service_correlation_node import CrossServiceCorrelationNode
    from app.services.agent.core.graph_nodes.automated_followup_investigations_node import AutomatedFollowupInvestigationsNode
    from app.services.agent.core.graph_nodes.dependency_chain_analysis_node import DependencyChainAnalysisNode
    from app.services.agent.core.graph_nodes.infrastructure_impact_assessment_node import InfrastructureImpactAssessmentNode
    from app.services.agent.core.graph_nodes.resource_utilization_correlation_node import ResourceUtilizationCorrelationNode
    from app.services.agent.core.graph_nodes.evidence_aggregation_node import EvidenceAggregationNode

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
        direct_filter_node = DirectFilterConstructionNode(self.config)
        single_stage_node = SingleStageFilterConstructionNode(self.config)
        context_aware_node = ContextAwareEnhancementNode(self.config)
        session_complete_node = SessionCompleteNode(self.config)
        filter_opt_node = FilterValidationOptimizationNode(self.config)
        primary_prep_node = PrimaryCallPreparationNode(self.config)
        execute_api_node = ExecuteLoggingAPINode(self.config)
        present_results_node = PresentResultsNode(self.config)
        response_analysis_node = ResponseAnalysisNode(self.config)
        md_analysis_node = MultiDimensionalAnalysisNode(self.config)
        decompose_node = ArchitectureAwareQueryDecompositionNode(self.config)
        dependency_node = DependencyStrategyNode(self.config)
        filter_planning_node = MultiStageFilterPlanningNode(self.config)
        filter_builder_node = ContextEnhancedFilterBuilderNode(self.config)
        auto_refine_node = AutoRefineFiltersNode(self.config)
        broaden_search_node = BroadenSearchNode(self.config)
        arch_discovery_node = ArchResourceDiscoveryNode(self.config)
        up_downstream_node = UpstreamDownstreamCheckNode(self.config)
        
        # Add nodes to the workflow
        workflow.add_node("user_query_input", user_query_node.execute)
        workflow.add_node("architecture_loader", architecture_loader_node.execute)
        workflow.add_node("intent_and_query_analysis", intent_analysis_node.execute)
        workflow.add_node("direct_filter", direct_filter_node.execute)
        workflow.add_node("single_stage_filter", single_stage_node.execute)
        workflow.add_node("context_aware_filter", context_aware_node.execute)
        workflow.add_node("session_complete", session_complete_node.execute)
        workflow.add_node("filter_optimization", filter_opt_node.execute)
        workflow.add_node("primary_call_prep", primary_prep_node.execute)
        workflow.add_node("execute_logging_api", execute_api_node.execute)
        workflow.add_node("present_results", present_results_node.execute)
        workflow.add_node("response_analysis", response_analysis_node.execute)
        workflow.add_node("multi_dimensional_analysis", md_analysis_node.execute)
        # Note: temporal_pattern_analysis node is registered below for Phase 5
        workflow.add_node("architecture_query_decomposition", decompose_node.execute)
        workflow.add_node("dependency_strategy", dependency_node.execute)
        workflow.add_node("multi_stage_filter_planning", filter_planning_node.execute)
        workflow.add_node("context_enhanced_filter_builder", filter_builder_node.execute)
        workflow.add_node("auto_refine_filters", auto_refine_node.execute)
        workflow.add_node("broaden_search", broaden_search_node.execute)
        workflow.add_node("arch_resource_discovery", arch_discovery_node.execute)
        workflow.add_node("upstream_downstream_check", up_downstream_node.execute)
        
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
        
        # Route to direct filter (D) for Phase 2 start, or to E in Phase 4
        workflow.add_conditional_edges(
            "intent_and_query_analysis",
            self._route_after_intent_analysis,
            {
                "proceed": "direct_filter",
                "needs_clarification": "direct_filter",
                "complex": "architecture_query_decomposition",
            }
        )
        # Phase 4: E -> J -> K -> L -> N
        workflow.add_edge("architecture_query_decomposition", "dependency_strategy")
        workflow.add_edge("dependency_strategy", "multi_stage_filter_planning")
        workflow.add_edge("multi_stage_filter_planning", "context_enhanced_filter_builder")
        workflow.add_edge("context_enhanced_filter_builder", "context_aware_filter")
        workflow.add_edge("direct_filter", "single_stage_filter")
        workflow.add_edge("single_stage_filter", "context_aware_filter")
        # Phase 2 continuation with Phase 3 (basic R + V): O -> P -> Q -> R -> V -> PP
        workflow.add_edge("context_aware_filter", "filter_optimization")
        workflow.add_edge("filter_optimization", "primary_call_prep")
        workflow.add_edge("primary_call_prep", "execute_logging_api")
        workflow.add_edge("execute_logging_api", "response_analysis")
        # Branch after R according to result_quality
        workflow.add_conditional_edges(
            "response_analysis",
            self._route_after_response_analysis,
            {
                "too_many": "auto_refine_filters",
                "too_few": "broaden_search",
                "empty": "arch_resource_discovery",
                "optimal": "multi_dimensional_analysis",
            }
        )
        # Refinement loops
        workflow.add_edge("auto_refine_filters", "context_aware_filter")
        workflow.add_edge("broaden_search", "context_aware_filter")
        workflow.add_edge("arch_resource_discovery", "upstream_downstream_check")
        workflow.add_edge("upstream_downstream_check", "context_aware_filter")
        # Phase 5: fan-out from V to V1/V2/V3/V5, each converging to PP
        try:
            from .graph_nodes.temporal_pattern_analysis_node import TemporalPatternAnalysisNode
            from .graph_nodes.error_clustering_node import ErrorClusteringNode
            from .graph_nodes.performance_metrics_node import PerformanceMetricsNode
            from .graph_nodes.anomaly_detection_node import AnomalyDetectionNode
            from .graph_nodes.architecture_correlation_node import ArchitectureCorrelationNode
        except ImportError:
            from app.services.agent.core.graph_nodes.temporal_pattern_analysis_node import TemporalPatternAnalysisNode
            from app.services.agent.core.graph_nodes.error_clustering_node import ErrorClusteringNode
            from app.services.agent.core.graph_nodes.performance_metrics_node import PerformanceMetricsNode
            from app.services.agent.core.graph_nodes.anomaly_detection_node import AnomalyDetectionNode
            from app.services.agent.core.graph_nodes.architecture_correlation_node import ArchitectureCorrelationNode
        v1_node = TemporalPatternAnalysisNode(self.config)
        v2_node = ErrorClusteringNode(self.config)
        v3_node = PerformanceMetricsNode(self.config)
        v5_node = AnomalyDetectionNode(self.config)
        v4_node = ArchitectureCorrelationNode(self.config)
        w_node = CrossServiceCorrelationNode(self.config)
        x_node = AutomatedFollowupInvestigationsNode(self.config)
        x1_node = DependencyChainAnalysisNode(self.config)
        x2_node = InfrastructureImpactAssessmentNode(self.config)
        x3_node = ResourceUtilizationCorrelationNode(self.config)
        y_node = EvidenceAggregationNode(self.config)
        workflow.add_node("temporal_pattern_analysis", v1_node.execute)
        workflow.add_node("error_clustering", v2_node.execute)
        workflow.add_node("performance_metrics", v3_node.execute)
        workflow.add_node("anomaly_detection", v5_node.execute)
        workflow.add_node("architecture_correlation", v4_node.execute)
        workflow.add_node("cross_service_correlation", w_node.execute)
        workflow.add_node("automated_followups", x_node.execute)
        workflow.add_node("dependency_chain_analysis", x1_node.execute)
        workflow.add_node("infrastructure_impact", x2_node.execute)
        workflow.add_node("resource_utilization", x3_node.execute)
        workflow.add_node("evidence_aggregation", y_node.execute)
        workflow.add_edge("multi_dimensional_analysis", "temporal_pattern_analysis")
        workflow.add_edge("multi_dimensional_analysis", "error_clustering")
        workflow.add_edge("multi_dimensional_analysis", "performance_metrics")
        workflow.add_edge("multi_dimensional_analysis", "anomaly_detection")
        workflow.add_edge("multi_dimensional_analysis", "architecture_correlation")
        workflow.add_edge("temporal_pattern_analysis", "cross_service_correlation")
        workflow.add_edge("error_clustering", "cross_service_correlation")
        workflow.add_edge("performance_metrics", "cross_service_correlation")
        workflow.add_edge("anomaly_detection", "cross_service_correlation")
        workflow.add_edge("architecture_correlation", "cross_service_correlation")
        workflow.add_edge("cross_service_correlation", "automated_followups")
        workflow.add_edge("automated_followups", "dependency_chain_analysis")
        workflow.add_edge("automated_followups", "infrastructure_impact")
        workflow.add_edge("automated_followups", "resource_utilization")
        workflow.add_edge("dependency_chain_analysis", "evidence_aggregation")
        workflow.add_edge("infrastructure_impact", "evidence_aggregation")
        workflow.add_edge("resource_utilization", "evidence_aggregation")
        workflow.add_edge("evidence_aggregation", "present_results")
        workflow.add_edge("present_results", "session_complete")
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
        Returns one of: 'needs_clarification', 'proceed', 'complex'."""
        if state.get("needs_clarification", False):
            return "needs_clarification"
        qt = (state.get("query_type") or "").strip().lower()
        if qt == "complex":
            return "complex"
        return "proceed"

    def _route_after_response_analysis(self, state: AgentState) -> str:
        """
        Route decision after response analysis node.
        Returns one of: 'too_many', 'too_few', 'empty', 'optimal'.
        """
        q = state.get("result_quality")
        if q in {"too_many", "too_few", "empty", "optimal"}:
            return q
        # Default to optimal if unspecified (defensive; R should always set it)
        return "optimal"
    
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
                from .graph_nodes.direct_filter_construction_node import DirectFilterConstructionNode
                from .graph_nodes.single_stage_filter_construction_node import SingleStageFilterConstructionNode
                from .graph_nodes.session_complete_node import SessionCompleteNode
            except Exception:
                # Fallback absolute imports
                from app.services.agent.core.graph_nodes.user_query_input_node import UserQueryInputNode
                from app.services.agent.core.architecture_loader_node import ArchitectureLoaderNode
                from app.services.agent.core.graph_nodes.intent_and_query_analysis_node import IntentAndQueryAnalysisNode
                from app.services.agent.core.graph_nodes.direct_filter_construction_node import DirectFilterConstructionNode
                from app.services.agent.core.graph_nodes.single_stage_filter_construction_node import SingleStageFilterConstructionNode
                from app.services.agent.core.graph_nodes.session_complete_node import SessionCompleteNode

            user_query_node = UserQueryInputNode(self.config)
            architecture_loader_node = ArchitectureLoaderNode(self.config)
            intent_node = IntentAndQueryAnalysisNode(self.config)
            direct_filter_node = DirectFilterConstructionNode(self.config)
            single_stage_node = SingleStageFilterConstructionNode(self.config)
            session_node = SessionCompleteNode(self.config)

            # Helper to emit a node event
            async def emit_node_event(node_key: str, title: str, status: str, data: Dict[str, Any]):
                yield {
                    "type": "node_event",
                    "node": node_key,
                    "title": title,
                    "status": status,
                    "data": data,
                    "state": state,
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
                "context_summary": arch_ctx.get("context_summary"),
                # Phase 4 repository summaries if available
                "topology": (arch_tool.get("topology") if isinstance(arch_tool, dict) else None),
                "service_registry": (arch_tool.get("service_registry") if isinstance(arch_tool, dict) else None),
                "data_flows": (arch_tool.get("data_flows") if isinstance(arch_tool, dict) else None),
                "infrastructure": (arch_tool.get("infrastructure") if isinstance(arch_tool, dict) else None),
                "performance": (arch_tool.get("performance") if isinstance(arch_tool, dict) else None),
                "failures": (arch_tool.get("failures") if isinstance(arch_tool, dict) else None),
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

            is_complex = ((state.get("query_type") or "").strip().lower() == "complex")

            # Phase 4: If complex, run E node before filter construction (temporary bridge to normal path)
            if (state.get("query_type") or "").strip().lower() == "complex":
                try:
                    from .graph_nodes.architecture_query_decomposition_node import ArchitectureAwareQueryDecompositionNode
                except Exception:
                    from app.services.agent.core.graph_nodes.architecture_query_decomposition_node import ArchitectureAwareQueryDecompositionNode
                e_node = ArchitectureAwareQueryDecompositionNode(self.config)
                async for evt in emit_node_event("architecture_query_decomposition", "Architecture-Aware Query Decomposition", "started", {
                    "note": "Decomposing complex query"
                }):
                    yield evt
                state = await e_node.execute(state)
                async for evt in emit_node_event("architecture_query_decomposition", "Architecture-Aware Query Decomposition", "completed", {
                    "anchors": len(((state.get("query_decomposition") or {}).get("anchors") or [])),
                    "flow_hint": len(((state.get("query_decomposition") or {}).get("flow_hint") or [])),
                }):
                    yield evt
                # J: Dependency-Based Strategy
                try:
                    from .graph_nodes.dependency_strategy_node import DependencyStrategyNode
                except Exception:
                    from app.services.agent.core.graph_nodes.dependency_strategy_node import DependencyStrategyNode
                j_node = DependencyStrategyNode(self.config)
                async for evt in emit_node_event("dependency_strategy", "Dependency Strategy", "started", {
                    "note": "Planning staged investigation"
                }):
                    yield evt
                state = await j_node.execute(state)
                async for evt in emit_node_event("dependency_strategy", "Dependency Strategy", "completed", {
                    "stages": len(state.get("investigation_plan") or [])
                }):
                    yield evt
                # K: Multi-Stage Filter Planning
                try:
                    from .graph_nodes.multi_stage_filter_planning_node import MultiStageFilterPlanningNode
                except Exception:
                    from app.services.agent.core.graph_nodes.multi_stage_filter_planning_node import MultiStageFilterPlanningNode
                k_node = MultiStageFilterPlanningNode(self.config)
                async for evt in emit_node_event("multi_stage_filter_planning", "Filter Planning", "started", {
                    "note": "Generating per-stage filter blueprint"
                }):
                    yield evt
                state = await k_node.execute(state)
                async for evt in emit_node_event("multi_stage_filter_planning", "Filter Planning", "completed", {
                    "stages": len(state.get("filter_plan") or [])
                }):
                    yield evt
                # L: Context-Enhanced Filter Builder
                try:
                    from .graph_nodes.context_enhanced_filter_builder_node import ContextEnhancedFilterBuilderNode
                except Exception:
                    from app.services.agent.core.graph_nodes.context_enhanced_filter_builder_node import ContextEnhancedFilterBuilderNode
                l_node = ContextEnhancedFilterBuilderNode(self.config)
                async for evt in emit_node_event("context_enhanced_filter_builder", "Context-Enhanced Filter Builder", "started", {
                    "note": "Translating plan to concrete Logging filter"
                }):
                    yield evt
                state = await l_node.execute(state)
                async for evt in emit_node_event("context_enhanced_filter_builder", "Context-Enhanced Filter Builder", "completed", {
                    "logging_filter": state.get("logging_filter")
                }):
                    yield evt
            # D/M: Simple path only; skip if complex (E/J/K/L already built the filter)
            if not is_complex:
                # D: Direct Filter Construction
                async for evt in emit_node_event("direct_filter", "Direct Filter Construction", "started", {
                    "note": "Building simple Logging filter from entities"
                }):
                    yield evt
                state = await direct_filter_node.execute(state)
                async for evt in emit_node_event("direct_filter", "Direct Filter Construction", "completed", {
                    "logging_filter": state.get("logging_filter"),
                    "order_by": state.get("order_by"),
                    "components": state.get("logging_filter_components"),
                }):
                    yield evt
                # M: Single-Stage Filter Construction
                async for evt in emit_node_event("single_stage_filter", "Single-Stage Filter Construction", "started", {
                    "note": "Adding HTTP status and identifier hints"
                }):
                    yield evt
                state = await single_stage_node.execute(state)
                async for evt in emit_node_event("single_stage_filter", "Single-Stage Filter Construction", "completed", {
                    "logging_filter": state.get("logging_filter"),
                    "components": state.get("logging_filter_components"),
                }):
                    yield evt
            # N: Context-Aware Enhancement
            async for evt in emit_node_event("context_aware_filter", "Context-Aware Enhancement", "started", {
                "note": "Leveraging architecture context to refine filter"
            }):
                yield evt
            try:
                from .graph_nodes.context_aware_enhancement_node import ContextAwareEnhancementNode
            except Exception:
                from app.services.agent.core.graph_nodes.context_aware_enhancement_node import ContextAwareEnhancementNode
            context_node = ContextAwareEnhancementNode(self.config)
            state = await context_node.execute(state)
            async for evt in emit_node_event("context_aware_filter", "Context-Aware Enhancement", "completed", {
                "logging_filter": state.get("logging_filter"),
                "components": state.get("logging_filter_components"),
                "context_enrichment": state.get("context_enrichment"),
            }):
                yield evt
            # O: Filter Validation & Optimization
            async for evt in emit_node_event("filter_optimization", "Filter Validation & Optimization", "started", {
                "note": "Deduplicating and merging filter clauses"
            }):
                yield evt
            try:
                from .graph_nodes.filter_validation_optimization_node import FilterValidationOptimizationNode
            except Exception:
                from app.services.agent.core.graph_nodes.filter_validation_optimization_node import FilterValidationOptimizationNode
            filter_opt_node = FilterValidationOptimizationNode(self.config)
            state = await filter_opt_node.execute(state)
            async for evt in emit_node_event("filter_optimization", "Filter Validation & Optimization", "completed", {
                "logging_filter": state.get("logging_filter"),
                "order_by": state.get("order_by"),
                "optimization": state.get("logging_filter_optimization"),
            }):
                yield evt
            # P: Primary API Call Preparation
            async for evt in emit_node_event("primary_call_prep", "Primary API Call Preparation", "started", {
                "note": "Assembling entries:list request parameters"
            }):
                yield evt
            try:
                from .graph_nodes.primary_call_preparation_node import PrimaryCallPreparationNode
            except Exception:
                from app.services.agent.core.graph_nodes.primary_call_preparation_node import PrimaryCallPreparationNode
            primary_prep_node = PrimaryCallPreparationNode(self.config)
            state = await primary_prep_node.execute(state)
            req = state.get("logging_request") or {}
            async for evt in emit_node_event("primary_call_prep", "Primary API Call Preparation", "completed", {
                "project_id": req.get("project_id"),
                "page_size": req.get("page_size"),
                "order_by": req.get("order_by"),
                "has_field_mask": bool(req.get("field_mask")),
                "resource_names": req.get("resource_names"),
            }):
                yield evt
            # Q: Execute Google Cloud Logging API (stream pages)
            async for evt in emit_node_event("execute_logging_api", "Execute Logging API", "started", {
                "note": "Calling entries:list and streaming pages",
                "page_size": (state.get("logging_request") or {}).get("page_size"),
                "order_by": (state.get("logging_request") or {}).get("order_by"),
            }):
                yield evt
            try:
                from ...gcp.logging_client import GCPLoggingClient
            except Exception:
                from app.services.gcp.logging_client import GCPLoggingClient
            client = GCPLoggingClient()
            req_opts = state.get("logging_request") or {}
            access_token = state.get("access_token") or ""
            total_returned = 0
            collected = []
            if not access_token:
                async for evt in emit_node_event("execute_logging_api", "Execute Logging API", "error", {
                    "message": "Missing access token"
                }):
                    yield evt
            else:
                async for pe in client.entries_list_stream(
                    access_token=access_token,
                    project_id=req_opts.get("project_id", ""),
                    filter_str=req_opts.get("filter"),
                    order_by=req_opts.get("order_by"),
                    page_size=req_opts.get("page_size"),
                    max_pages=req_opts.get("max_pages"),
                    max_entries=req_opts.get("max_entries"),
                    field_mask=req_opts.get("field_mask"),
                    resource_names=req_opts.get("resource_names"),
                ):
                    if pe.get("type") == "page":
                        total_returned += pe.get("returned", 0)
                        entries = pe.get("entries", [])
                        collected.extend(entries)
                        sample = []
                        for e in entries[:3]:
                            sample.append({
                                "timestamp": e.get("timestamp"),
                                "severity": e.get("severity"),
                                "message": e.get("message"),
                            })
                        async for evt in emit_node_event(
                            "execute_logging_api", "Execute Logging API", "page",
                            {"page_index": pe.get("page_index"), "returned": pe.get("returned"), "total_returned": total_returned, "sample": sample},
                        ):
                            yield evt
                    elif pe.get("type") == "end":
                        async for evt in emit_node_event(
                            "execute_logging_api", "Execute Logging API", "completed",
                            {"page_count": pe.get("page_count"), "returned": pe.get("returned"), "next_page_token": pe.get("next_page_token")},
                        ):
                            yield evt
                    elif pe.get("type") == "error":
                        async for evt in emit_node_event(
                            "execute_logging_api", "Execute Logging API", "error",
                            {"message": pe.get("message"), "status": pe.get("status")},
                        ):
                            yield evt
                        break
            # Store a capped set of results into state for UI
            max_store = 100
            updated_relevant = (collected[:max_store]) if collected else []
            state = state.copy()
            tool_results = state.get("tool_results") or {}
            tool_results.update({
                "logging_api": {"returned": len(collected), "stored": len(updated_relevant)}
            })
            state.update({"relevant_logs": updated_relevant, "tool_results": tool_results})

            # R: Response Analysis (basic)
            try:
                from .graph_nodes.response_analysis_node import ResponseAnalysisNode
            except Exception:
                from app.services.agent.core.graph_nodes.response_analysis_node import ResponseAnalysisNode
            ran_node = ResponseAnalysisNode(self.config)
            async for evt in emit_node_event("response_analysis", "Response Analysis", "started", {
                "note": "Assessing result quality and patterns"
            }):
                yield evt
            state = await ran_node.execute(state)
            async for evt in emit_node_event("response_analysis", "Response Analysis", "completed", {
                "result_quality": state.get("result_quality"),
                "result_stats": state.get("result_stats"),
            }):
                yield evt

            # Phase 3 loops: iterate based on result_quality until optimal or caps reached
            try:
                from .graph_nodes.auto_refine_filters_node import AutoRefineFiltersNode
                from .graph_nodes.broaden_search_node import BroadenSearchNode
                from .graph_nodes.arch_resource_discovery_node import ArchResourceDiscoveryNode
                from .graph_nodes.upstream_downstream_check_node import UpstreamDownstreamCheckNode
                from .graph_nodes.context_aware_enhancement_node import ContextAwareEnhancementNode
                from .graph_nodes.filter_validation_optimization_node import FilterValidationOptimizationNode
                from .graph_nodes.primary_call_preparation_node import PrimaryCallPreparationNode
            except Exception:
                from app.services.agent.core.graph_nodes.auto_refine_filters_node import AutoRefineFiltersNode
                from app.services.agent.core.graph_nodes.broaden_search_node import BroadenSearchNode
                from app.services.agent.core.graph_nodes.arch_resource_discovery_node import ArchResourceDiscoveryNode
                from app.services.agent.core.graph_nodes.upstream_downstream_check_node import UpstreamDownstreamCheckNode
                from app.services.agent.core.graph_nodes.context_aware_enhancement_node import ContextAwareEnhancementNode
                from app.services.agent.core.graph_nodes.filter_validation_optimization_node import FilterValidationOptimizationNode
                from app.services.agent.core.graph_nodes.primary_call_preparation_node import PrimaryCallPreparationNode

            refine_node = AutoRefineFiltersNode(self.config)
            broaden_node = BroadenSearchNode(self.config)
            arch_disc_node = ArchResourceDiscoveryNode(self.config)
            up_down_node = UpstreamDownstreamCheckNode(self.config)
            ctx_node = ContextAwareEnhancementNode(self.config)
            opt_node = FilterValidationOptimizationNode(self.config)
            prep_node = PrimaryCallPreparationNode(self.config)

            # Caps (fallback defaults if absent)
            phase3 = getattr(self.config, 'phase3', None)
            max_refines = getattr(phase3, 'max_refinements', 2) if phase3 else 2
            max_broadens = getattr(phase3, 'max_broadenings', 2) if phase3 else 2
            max_arch = 1
            loop_guard_max = 6
            refine_count = int(state.get('refinement_iterations') or 0)
            broaden_count = int(state.get('broadening_iterations') or 0)
            arch_count = int(state.get('arch_iterations') or 0)
            loop_guard = 0

            while True:
                quality = (state.get('result_quality') or 'optimal')
                if quality == 'optimal':
                    break
                if loop_guard >= loop_guard_max:
                    async for evt in emit_node_event("response_analysis", "Response Analysis", "completed", {
                        "note": "Loop guard reached; proceeding to analysis",
                        "result_quality": quality,
                    }):
                        yield evt
                    break

                if quality == 'too_many':
                    if refine_count >= max_refines:
                        async for evt in emit_node_event("auto_refine_filters", "Auto-Refine Filters", "completed", {
                            "note": "Max refinements reached; skipping"
                        }):
                            yield evt
                    else:
                        async for evt in emit_node_event("auto_refine_filters", "Auto-Refine Filters", "started", {
                            "reason": "too_many_results"
                        }):
                            yield evt
                        state = await refine_node.execute(state)
                        refine_count += 1
                        state.update({'refinement_iterations': refine_count})
                        async for evt in emit_node_event("auto_refine_filters", "Auto-Refine Filters", "completed", {
                            "iterations": refine_count
                        }):
                            yield evt

                elif quality == 'too_few':
                    if broaden_count >= max_broadens:
                        async for evt in emit_node_event("broaden_search", "Broaden Search", "completed", {
                            "note": "Max broadenings reached; skipping"
                        }):
                            yield evt
                    else:
                        async for evt in emit_node_event("broaden_search", "Broaden Search", "started", {
                            "reason": "too_few_results"
                        }):
                            yield evt
                        state = await broaden_node.execute(state)
                        broaden_count += 1
                        state.update({'broadening_iterations': broaden_count})
                        async for evt in emit_node_event("broaden_search", "Broaden Search", "completed", {
                            "iterations": broaden_count
                        }):
                            yield evt

                elif quality == 'empty':
                    if arch_count >= max_arch:
                        async for evt in emit_node_event("arch_resource_discovery", "Architecture-Guided Discovery", "completed", {
                            "note": "Max arch discovery reached; skipping"
                        }):
                            yield evt
                    else:
                        async for evt in emit_node_event("arch_resource_discovery", "Architecture-Guided Discovery", "started", {
                            "note": "Discovering related resources"
                        }):
                            yield evt
                        state = await arch_disc_node.execute(state)
                        async for evt in emit_node_event("arch_resource_discovery", "Architecture-Guided Discovery", "completed", {
                            "discovered": len(state.get('discovered_resources') or [])
                        }):
                            yield evt
                        async for evt in emit_node_event("upstream_downstream_check", "Upstream/Downstream Check", "started", {
                            "note": "Checking neighbors"
                        }):
                            yield evt
                        state = await up_down_node.execute(state)
                        async for evt in emit_node_event("upstream_downstream_check", "Upstream/Downstream Check", "completed", {
                            "ok": state.get('up_downstream_checked')
                        }):
                            yield evt
                        arch_count += 1
                        state.update({'arch_iterations': arch_count})

                # Rebuild filters: N -> O -> P
                async for evt in emit_node_event("context_aware_filter", "Context-Aware Enhancement", "started", {
                    "note": "Re-applying context-aware enrichment"
                }):
                    yield evt
                state = await ctx_node.execute(state)
                async for evt in emit_node_event("context_aware_filter", "Context-Aware Enhancement", "completed", {
                    "note": "Done"
                }):
                    yield evt

                async for evt in emit_node_event("filter_optimization", "Filter Validation & Optimization", "started", {
                    "note": "Optimizing filter"
                }):
                    yield evt
                state = await opt_node.execute(state)
                async for evt in emit_node_event("filter_optimization", "Filter Validation & Optimization", "completed", {
                    "note": "Done"
                }):
                    yield evt

                async for evt in emit_node_event("primary_call_prep", "Primary API Call Preparation", "started", {
                    "note": "Assembling updated request"
                }):
                    yield evt
                state = await prep_node.execute(state)
                req = state.get("logging_request") or {}
                async for evt in emit_node_event("primary_call_prep", "Primary API Call Preparation", "completed", {
                    "project_id": req.get("project_id"),
                    "page_size": req.get("page_size"),
                    "order_by": req.get("order_by"),
                }):
                    yield evt

                # Execute Q again
                async for evt in emit_node_event("execute_logging_api", "Execute Logging API", "started", {
                    "note": "Re-executing entries:list"
                }):
                    yield evt
                req_opts = state.get("logging_request") or {}
                access_token = state.get("access_token") or ""
                total_returned = 0
                collected = []
                if not access_token:
                    async for evt in emit_node_event("execute_logging_api", "Execute Logging API", "error", {
                        "message": "Missing access token"
                    }):
                        yield evt
                else:
                    async for pe in client.entries_list_stream(
                        access_token=access_token,
                        project_id=req_opts.get("project_id", ""),
                        filter_str=req_opts.get("filter"),
                        order_by=req_opts.get("order_by"),
                        page_size=req_opts.get("page_size"),
                        max_pages=req_opts.get("max_pages"),
                        max_entries=req_opts.get("max_entries"),
                        field_mask=req_opts.get("field_mask"),
                        resource_names=req_opts.get("resource_names"),
                    ):
                        if pe.get("type") == "page":
                            total_returned += pe.get("returned", 0)
                            entries = pe.get("entries", [])
                            collected.extend(entries)
                            sample = []
                            for e in entries[:3]:
                                sample.append({
                                    "timestamp": e.get("timestamp"),
                                    "severity": e.get("severity"),
                                    "message": e.get("message"),
                                })
                            async for evt in emit_node_event(
                                "execute_logging_api", "Execute Logging API", "page",
                                {"page_index": pe.get("page_index"), "returned": pe.get("returned"), "total_returned": total_returned, "sample": sample},
                            ):
                                yield evt
                        elif pe.get("type") == "end":
                            async for evt in emit_node_event(
                                "execute_logging_api", "Execute Logging API", "completed",
                                {"page_count": pe.get("page_count"), "returned": pe.get("returned"), "next_page_token": pe.get("next_page_token")},
                            ):
                                yield evt
                        elif pe.get("type") == "error":
                            async for evt in emit_node_event(
                                "execute_logging_api", "Execute Logging API", "error",
                                {"message": pe.get("message"), "status": pe.get("status")},
                            ):
                                yield evt
                            break

                # Store results
                max_store = 100
                updated_relevant = (collected[:max_store]) if collected else []
                state = state.copy()
                tool_results = state.get("tool_results") or {}
                tool_results.update({
                    "logging_api": {"returned": len(collected), "stored": len(updated_relevant)}
                })
                state.update({"relevant_logs": updated_relevant, "tool_results": tool_results})

                # Re-run R
                async for evt in emit_node_event("response_analysis", "Response Analysis", "started", {
                    "note": "Re-assessing result quality"
                }):
                    yield evt
                state = await ran_node.execute(state)
                async for evt in emit_node_event("response_analysis", "Response Analysis", "completed", {
                    "result_quality": state.get("result_quality"),
                    "result_stats": state.get("result_stats"),
                }):
                    yield evt

                loop_guard += 1

            # V: Multi-Dimensional Analysis (basic)
            try:
                from .graph_nodes.multi_dimensional_analysis_node import MultiDimensionalAnalysisNode
            except Exception:
                from app.services.agent.core.graph_nodes.multi_dimensional_analysis_node import MultiDimensionalAnalysisNode
            v_node = MultiDimensionalAnalysisNode(self.config)
            async for evt in emit_node_event("multi_dimensional_analysis", "Multi-Dimensional Analysis", "started", {
                "note": "Computing temporal density, error rates, top messages"
            }):
                yield evt
            state = await v_node.execute(state)
            async for evt in emit_node_event("multi_dimensional_analysis", "Multi-Dimensional Analysis", "completed", {
                "summary": state.get("md_summary")
            }):
                yield evt

            # V1: Temporal Pattern Analysis
            try:
                from .graph_nodes.temporal_pattern_analysis_node import TemporalPatternAnalysisNode
            except Exception:
                from app.services.agent.core.graph_nodes.temporal_pattern_analysis_node import TemporalPatternAnalysisNode
            v1_node = TemporalPatternAnalysisNode(self.config)
            async for evt in emit_node_event("temporal_pattern_analysis", "Temporal Pattern Analysis", "started", {
                "note": "Detecting spikes and trends"
            }):
                yield evt
            state = await v1_node.execute(state)
            async for evt in emit_node_event("temporal_pattern_analysis", "Temporal Pattern Analysis", "completed", {
                "spike_count": len(((state.get("temporal_trends") or {}).get("spikes") or []))
            }):
                yield evt
            # V2: Error Clustering & Classification
            try:
                from .graph_nodes.error_clustering_node import ErrorClusteringNode
            except Exception:
                from app.services.agent.core.graph_nodes.error_clustering_node import ErrorClusteringNode
            v2_node = ErrorClusteringNode(self.config)
            async for evt in emit_node_event("error_clustering", "Error Clustering", "started", {
                "note": "Grouping errors by normalized patterns"
            }):
                yield evt
            state = await v2_node.execute(state)
            async for evt in emit_node_event("error_clustering", "Error Clustering", "completed", {
                "cluster_count": len(state.get("error_clusters") or [])
            }):
                yield evt
            # V3: Performance Metrics Extraction
            try:
                from .graph_nodes.performance_metrics_node import PerformanceMetricsNode
            except Exception:
                from app.services.agent.core.graph_nodes.performance_metrics_node import PerformanceMetricsNode
            v3_node = PerformanceMetricsNode(self.config)
            async for evt in emit_node_event("performance_metrics", "Performance Metrics", "started", {
                "note": "Computing latency percentiles and error rate"
            }):
                yield evt
            state = await v3_node.execute(state)
            async for evt in emit_node_event("performance_metrics", "Performance Metrics", "completed", {
                "p95_ms": ((state.get("performance_metrics") or {}).get("p95_ms"))
            }):
                yield evt
            # V5: Anomaly Detection
            try:
                from .graph_nodes.anomaly_detection_node import AnomalyDetectionNode
            except Exception:
                from app.services.agent.core.graph_nodes.anomaly_detection_node import AnomalyDetectionNode
            v5_node = AnomalyDetectionNode(self.config)
            async for evt in emit_node_event("anomaly_detection", "Anomaly Detection", "started", {
                "note": "Comparing metrics/spikes against baselines"
            }):
                yield evt
            state = await v5_node.execute(state)
            async for evt in emit_node_event("anomaly_detection", "Anomaly Detection", "completed", {
                "anomaly_count": len(state.get("anomalies") or [])
            }):
                yield evt
            # V4: Architecture-Based Correlation (streamed sequentially)
            try:
                from .graph_nodes.architecture_correlation_node import ArchitectureCorrelationNode
            except Exception:
                from app.services.agent.core.graph_nodes.architecture_correlation_node import ArchitectureCorrelationNode
            v4_node = ArchitectureCorrelationNode(self.config)
            async for evt in emit_node_event("architecture_correlation", "Architecture Correlation", "started", {
                "note": "Correlating signals across services"
            }):
                yield evt
            state = await v4_node.execute(state)
            async for evt in emit_node_event("architecture_correlation", "Architecture Correlation", "completed", {
                "finding_count": len(state.get("correlation_findings") or [])
            }):
                yield evt

            # PP: Present Results
            try:
                from .graph_nodes.present_results_node import PresentResultsNode
            except Exception:
                from app.services.agent.core.graph_nodes.present_results_node import PresentResultsNode
            present_node = PresentResultsNode(self.config)
            async for evt in emit_node_event("present_results", "Present Results", "started", {
                "note": "Formatting results for UI"
            }):
                yield evt
            state = await present_node.execute(state)
            async for evt in emit_node_event("present_results", "Present Results", "completed", {
                "total": (state.get("presentation") or {}).get("total"),
                "severity_breakdown": (state.get("presentation") or {}).get("severity_breakdown"),
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
