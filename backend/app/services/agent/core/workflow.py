"""LangGraph workflow wiring for the GCP Log Investigation Agent.

The graph is intentionally organised in phases so the full investigation
story can be read straight down the file:

1. Intake & context bootstrapping – capture the user's question and load
   reusable project memory.
2. Filter design & execution – build the Logging API request, call the API,
   and analyse the raw response quality.
3. Result presentation & quality loops – refine filters, branch into
   architecture-aware planning when required, and aggregate findings.
4. Advanced analysis & clarification fan-out – run deeper analytics and, if
   confidence drops, gather additional input from the user before continuing.
5. Context & session persistence – stash the investigation artefacts so the
   next query resumes with rich context.

The comments around each `add_edge` and `add_conditional_edges` call describe
how control flows between phases, making the graph readable without needing to
step through each node implementation.
"""

import asyncio
import copy
import importlib
import logging
from collections import deque
from contextlib import suppress
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast

from langgraph.graph import END, StateGraph
# Clarification checkpoints are stored in memory; replace with durable storage when scaling horizontally.

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
    from .graph_nodes.temporal_pattern_analysis_node import TemporalPatternAnalysisNode
    from .graph_nodes.error_clustering_node import ErrorClusteringNode
    from .graph_nodes.performance_metrics_node import PerformanceMetricsNode
    from .graph_nodes.anomaly_detection_node import AnomalyDetectionNode
    from .graph_nodes.architecture_correlation_node import ArchitectureCorrelationNode
    from .graph_nodes.cross_service_correlation_node import CrossServiceCorrelationNode
    from .graph_nodes.automated_followup_investigations_node import AutomatedFollowupInvestigationsNode
    from .graph_nodes.dependency_chain_analysis_node import DependencyChainAnalysisNode
    from .graph_nodes.infrastructure_impact_assessment_node import InfrastructureImpactAssessmentNode
    from .graph_nodes.resource_utilization_correlation_node import ResourceUtilizationCorrelationNode
    from .graph_nodes.evidence_aggregation_node import EvidenceAggregationNode
    from .graph_nodes.confidence_assessment_node import ConfidenceAssessmentNode
    from .graph_nodes.confidence_decision_router_node import ConfidenceDecisionRouterNode
    from .graph_nodes.hypothesis_generation_node import HypothesisGenerationNode
    from .graph_nodes.targeted_clarification_node import TargetedClarificationNode
    from .graph_nodes.root_cause_synthesis_node import RootCauseSynthesisNode
    from .graph_nodes.additional_api_queries_node import AdditionalApiQueriesNode
    from .graph_nodes.clarification_engine_node import ClarificationEngineNode
    from .graph_nodes.contextual_question_generator_node import ContextualQuestionGeneratorNode
    from .graph_nodes.wait_for_user_response_node import WaitForUserResponseNode
    from .graph_nodes.architecture_specific_question_node import ArchitectureSpecificQuestionNode
    from .graph_nodes.timeline_reconstruction_node import TimelineReconstructionNode
    from .graph_nodes.impact_analysis_node import ImpactAnalysisNode
    from .graph_nodes.critical_path_identification_node import CriticalPathIdentificationNode
    from .graph_nodes.cascade_failure_prediction_node import CascadeFailurePredictionNode
    from .graph_nodes.evidence_compilation_node import EvidenceCompilationNode
    from .graph_nodes.actionable_recommendations_node import ActionableRecommendationsNode
    from .graph_nodes.response_formatting_node import ResponseFormattingNode
    from .graph_nodes.context_memory_update_node import ContextMemoryUpdateNode
    from .graph_nodes.query_history_node import QueryHistoryNode
    from .graph_nodes.user_preferences_node import UserPreferencesNode
    from .graph_nodes.session_state_node import SessionStateNode
    from .graph_nodes.learning_repository_node import LearningRepositoryNode
    from .graph_nodes.team_knowledge_node import TeamKnowledgeNode
    from .graph_nodes.architecture_pattern_learning_node import ArchitecturePatternLearningNode
    from .graph_nodes.user_satisfaction_node import UserSatisfactionNode
    from .graph_nodes.drill_down_investigation_node import DrillDownInvestigationNode
    from .graph_nodes.alternative_analysis_path_node import AlternativeAnalysisPathNode
    from .graph_nodes.preventive_analysis_node import PreventiveAnalysisNode
    from .graph_nodes.proactive_monitoring_setup_node import ProactiveMonitoringSetupNode
    from .graph_nodes.architecture_loader_agent_node import ArchitectureLoaderAgentNode
    from .graph_nodes.query_classifier_node import QueryClassifierNode
    from .graph_nodes.investigation_planner_node import InvestigationPlannerNode
    from .graph_nodes.filter_architect_node import FilterArchitectNode
    from .graph_nodes.api_orchestrator_node import APIOrchestratorNode
    from .graph_nodes.correlation_engine_node import CorrelationEngineNode
    from .graph_nodes.pattern_analyzer_node import PatternAnalyzerNode
    from .graph_nodes.synthesis_engine_node import SynthesisEngineNode
    from .graph_nodes.recommendation_engine_node import RecommendationEngineNode
    from .graph_nodes.context_manager_node import ContextManagerNode
    from .graph_nodes.performance_optimization_node import PerformanceOptimizationNode
    from .graph_nodes.real_time_stream_analysis_node import RealTimeStreamAnalysisNode
    from .graph_nodes.predictive_analytics_node import PredictiveAnalyticsNode
    from .graph_nodes.ml_pattern_recognition_node import MLPatternRecognitionNode
    from .graph_nodes.cross_project_learning_node import CrossProjectLearningNode
    from .graph_nodes.automated_remediation_node import AutomatedRemediationNode
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
    from app.services.agent.core.graph_nodes.temporal_pattern_analysis_node import TemporalPatternAnalysisNode
    from app.services.agent.core.graph_nodes.error_clustering_node import ErrorClusteringNode
    from app.services.agent.core.graph_nodes.performance_metrics_node import PerformanceMetricsNode
    from app.services.agent.core.graph_nodes.anomaly_detection_node import AnomalyDetectionNode
    from app.services.agent.core.graph_nodes.architecture_correlation_node import ArchitectureCorrelationNode
    from app.services.agent.core.graph_nodes.cross_service_correlation_node import CrossServiceCorrelationNode
    from app.services.agent.core.graph_nodes.automated_followup_investigations_node import AutomatedFollowupInvestigationsNode
    from app.services.agent.core.graph_nodes.dependency_chain_analysis_node import DependencyChainAnalysisNode
    from app.services.agent.core.graph_nodes.infrastructure_impact_assessment_node import InfrastructureImpactAssessmentNode
    from app.services.agent.core.graph_nodes.resource_utilization_correlation_node import ResourceUtilizationCorrelationNode
    from app.services.agent.core.graph_nodes.evidence_aggregation_node import EvidenceAggregationNode
    from app.services.agent.core.graph_nodes.confidence_assessment_node import ConfidenceAssessmentNode
    from app.services.agent.core.graph_nodes.confidence_decision_router_node import ConfidenceDecisionRouterNode
    from app.services.agent.core.graph_nodes.hypothesis_generation_node import HypothesisGenerationNode
    from app.services.agent.core.graph_nodes.targeted_clarification_node import TargetedClarificationNode
    from app.services.agent.core.graph_nodes.root_cause_synthesis_node import RootCauseSynthesisNode
    from app.services.agent.core.graph_nodes.additional_api_queries_node import AdditionalApiQueriesNode
    from app.services.agent.core.graph_nodes.clarification_engine_node import ClarificationEngineNode
    from app.services.agent.core.graph_nodes.contextual_question_generator_node import ContextualQuestionGeneratorNode
    from app.services.agent.core.graph_nodes.wait_for_user_response_node import WaitForUserResponseNode
    from app.services.agent.core.graph_nodes.architecture_specific_question_node import ArchitectureSpecificQuestionNode
    from app.services.agent.core.graph_nodes.timeline_reconstruction_node import TimelineReconstructionNode
    from app.services.agent.core.graph_nodes.impact_analysis_node import ImpactAnalysisNode
    from app.services.agent.core.graph_nodes.critical_path_identification_node import CriticalPathIdentificationNode
    from app.services.agent.core.graph_nodes.cascade_failure_prediction_node import CascadeFailurePredictionNode
    from app.services.agent.core.graph_nodes.evidence_compilation_node import EvidenceCompilationNode
    from app.services.agent.core.graph_nodes.actionable_recommendations_node import ActionableRecommendationsNode
    from app.services.agent.core.graph_nodes.response_formatting_node import ResponseFormattingNode
    from app.services.agent.core.graph_nodes.context_memory_update_node import ContextMemoryUpdateNode
    from app.services.agent.core.graph_nodes.query_history_node import QueryHistoryNode
    from app.services.agent.core.graph_nodes.user_preferences_node import UserPreferencesNode
    from app.services.agent.core.graph_nodes.session_state_node import SessionStateNode
    from app.services.agent.core.graph_nodes.learning_repository_node import LearningRepositoryNode
    from app.services.agent.core.graph_nodes.team_knowledge_node import TeamKnowledgeNode
    from app.services.agent.core.graph_nodes.architecture_pattern_learning_node import ArchitecturePatternLearningNode
    from app.services.agent.core.graph_nodes.user_satisfaction_node import UserSatisfactionNode
    from app.services.agent.core.graph_nodes.drill_down_investigation_node import DrillDownInvestigationNode
    from app.services.agent.core.graph_nodes.alternative_analysis_path_node import AlternativeAnalysisPathNode
    from app.services.agent.core.graph_nodes.preventive_analysis_node import PreventiveAnalysisNode
    from app.services.agent.core.graph_nodes.proactive_monitoring_setup_node import ProactiveMonitoringSetupNode
    from app.services.agent.core.graph_nodes.architecture_loader_agent_node import ArchitectureLoaderAgentNode
    from app.services.agent.core.graph_nodes.query_classifier_node import QueryClassifierNode
    from app.services.agent.core.graph_nodes.investigation_planner_node import InvestigationPlannerNode
    from app.services.agent.core.graph_nodes.filter_architect_node import FilterArchitectNode
    from app.services.agent.core.graph_nodes.api_orchestrator_node import APIOrchestratorNode
    from app.services.agent.core.graph_nodes.correlation_engine_node import CorrelationEngineNode
    from app.services.agent.core.graph_nodes.pattern_analyzer_node import PatternAnalyzerNode
    from app.services.agent.core.graph_nodes.synthesis_engine_node import SynthesisEngineNode
    from app.services.agent.core.graph_nodes.recommendation_engine_node import RecommendationEngineNode
    from app.services.agent.core.graph_nodes.context_manager_node import ContextManagerNode
    from app.services.agent.core.graph_nodes.real_time_stream_analysis_node import RealTimeStreamAnalysisNode
    from app.services.agent.core.graph_nodes.predictive_analytics_node import PredictiveAnalyticsNode
    from app.services.agent.core.graph_nodes.ml_pattern_recognition_node import MLPatternRecognitionNode
    from app.services.agent.core.graph_nodes.cross_project_learning_node import CrossProjectLearningNode
    from app.services.agent.core.graph_nodes.automated_remediation_node import AutomatedRemediationNode
    from app.services.agent.core.graph_nodes.performance_optimization_node import PerformanceOptimizationNode
    from app.services.agent.core.graph_nodes.real_time_stream_analysis_node import RealTimeStreamAnalysisNode
    from app.services.agent.core.graph_nodes.predictive_analytics_node import PredictiveAnalyticsNode
    from app.services.agent.core.graph_nodes.ml_pattern_recognition_node import MLPatternRecognitionNode
    from app.services.agent.core.graph_nodes.cross_project_learning_node import CrossProjectLearningNode
    from app.services.agent.core.graph_nodes.automated_remediation_node import AutomatedRemediationNode
    from app.services.agent.core.graph_nodes.performance_optimization_node import PerformanceOptimizationNode

logger = logging.getLogger(__name__)


# Descriptive metadata for each workflow node used when wiring the LangGraph and emitting UI events.
NODE_SPECS: Dict[str, Dict[str, str]] = {
    # Intake & clarification setup
    "user_query_input": {
        "module": "graph_nodes.user_query_input_node",
        "class": "UserQueryInputNode",
        "title": "User Query Input",
    },
    "architecture_loader": {
        "module": "architecture_loader_node",
        "class": "ArchitectureLoaderNode",
        "title": "Load Project Architecture",
    },
    "architecture_loader_agent": {
        "module": "graph_nodes.architecture_loader_agent_node",
        "class": "ArchitectureLoaderAgentNode",
        "title": "Architecture Loader Agent",
    },
    "intent_and_query_analysis": {
        "module": "graph_nodes.intent_and_query_analysis_node",
        "class": "IntentAndQueryAnalysisNode",
        "title": "Intent & Query Analysis",
    },
    "query_classifier": {
        "module": "graph_nodes.query_classifier_node",
        "class": "QueryClassifierNode",
        "title": "Query Classifier",
    },
    "clarification_engine": {
        "module": "graph_nodes.clarification_engine_node",
        "class": "ClarificationEngineNode",
        "title": "Clarification Engine",
    },
    "contextual_questions": {
        "module": "graph_nodes.contextual_question_generator_node",
        "class": "ContextualQuestionGeneratorNode",
        "title": "Generate Contextual Questions",
    },
    "architecture_questions": {
        "module": "graph_nodes.architecture_specific_question_node",
        "class": "ArchitectureSpecificQuestionNode",
        "title": "Architecture-Specific Questions",
    },
    "wait_for_user_response": {
        "module": "graph_nodes.wait_for_user_response_node",
        "class": "WaitForUserResponseNode",
        "title": "Wait For User Response",
    },
    # Filter construction & execution
    "direct_filter": {
        "module": "graph_nodes.direct_filter_construction_node",
        "class": "DirectFilterConstructionNode",
        "title": "Direct Filter Construction",
    },
    "single_stage_filter": {
        "module": "graph_nodes.single_stage_filter_construction_node",
        "class": "SingleStageFilterConstructionNode",
        "title": "Single-Stage Filter Construction",
    },
    "architecture_query_decomposition": {
        "module": "graph_nodes.architecture_query_decomposition_node",
        "class": "ArchitectureAwareQueryDecompositionNode",
        "title": "Architecture-Aware Query Decomposition",
    },
    "investigation_planner": {
        "module": "graph_nodes.investigation_planner_node",
        "class": "InvestigationPlannerNode",
        "title": "Investigation Planner",
    },
    "dependency_strategy": {
        "module": "graph_nodes.dependency_strategy_node",
        "class": "DependencyStrategyNode",
        "title": "Dependency Strategy",
    },
    "multi_stage_filter_planning": {
        "module": "graph_nodes.multi_stage_filter_planning_node",
        "class": "MultiStageFilterPlanningNode",
        "title": "Multi-Stage Filter Planning",
    },
    "context_enhanced_filter_builder": {
        "module": "graph_nodes.context_enhanced_filter_builder_node",
        "class": "ContextEnhancedFilterBuilderNode",
        "title": "Context-Enhanced Filter Builder",
    },
    "filter_architect": {
        "module": "graph_nodes.filter_architect_node",
        "class": "FilterArchitectNode",
        "title": "Filter Architect",
    },
    "context_aware_filter": {
        "module": "graph_nodes.context_aware_enhancement_node",
        "class": "ContextAwareEnhancementNode",
        "title": "Context-Aware Enhancement",
    },
    "filter_optimization": {
        "module": "graph_nodes.filter_validation_optimization_node",
        "class": "FilterValidationOptimizationNode",
        "title": "Filter Validation & Optimization",
    },
    "primary_call_prep": {
        "module": "graph_nodes.primary_call_preparation_node",
        "class": "PrimaryCallPreparationNode",
        "title": "Primary API Call Preparation",
    },
    "api_orchestrator": {
        "module": "graph_nodes.api_orchestrator_node",
        "class": "APIOrchestratorNode",
        "title": "API Orchestrator",
    },
    "execute_logging_api": {
        "module": "graph_nodes.execute_logging_api_node",
        "class": "ExecuteLoggingAPINode",
        "title": "Execute Logging API",
    },
    "performance_optimization": {
        "module": "graph_nodes.performance_optimization_node",
        "class": "PerformanceOptimizationNode",
        "title": "Performance Optimization",
    },
    "response_analysis": {
        "module": "graph_nodes.response_analysis_node",
        "class": "ResponseAnalysisNode",
        "title": "Response Analysis",
    },
    "auto_refine_filters": {
        "module": "graph_nodes.auto_refine_filters_node",
        "class": "AutoRefineFiltersNode",
        "title": "Auto-Refine Filters",
    },
    "broaden_search": {
        "module": "graph_nodes.broaden_search_node",
        "class": "BroadenSearchNode",
        "title": "Broaden Search",
    },
    "arch_resource_discovery": {
        "module": "graph_nodes.arch_resource_discovery_node",
        "class": "ArchResourceDiscoveryNode",
        "title": "Architecture-Guided Resource Discovery",
    },
    "upstream_downstream_check": {
        "module": "graph_nodes.upstream_downstream_check_node",
        "class": "UpstreamDownstreamCheckNode",
        "title": "Upstream/Downstream Check",
    },
    # Advanced analysis and post-processing fan-out
    "multi_dimensional_analysis": {
        "module": "graph_nodes.multi_dimensional_analysis_node",
        "class": "MultiDimensionalAnalysisNode",
        "title": "Multi-Dimensional Analysis",
    },
    "temporal_pattern_analysis": {
        "module": "graph_nodes.temporal_pattern_analysis_node",
        "class": "TemporalPatternAnalysisNode",
        "title": "Temporal Pattern Analysis",
    },
    "error_clustering": {
        "module": "graph_nodes.error_clustering_node",
        "class": "ErrorClusteringNode",
        "title": "Error Clustering",
    },
    "performance_metrics": {
        "module": "graph_nodes.performance_metrics_node",
        "class": "PerformanceMetricsNode",
        "title": "Performance Metrics",
    },
    "anomaly_detection": {
        "module": "graph_nodes.anomaly_detection_node",
        "class": "AnomalyDetectionNode",
        "title": "Anomaly Detection",
    },
    "pattern_analyzer": {
        "module": "graph_nodes.pattern_analyzer_node",
        "class": "PatternAnalyzerNode",
        "title": "Pattern Analyzer",
    },
    "ml_pattern_recognition": {
        "module": "graph_nodes.ml_pattern_recognition_node",
        "class": "MLPatternRecognitionNode",
        "title": "ML Pattern Recognition",
    },
    "architecture_correlation": {
        "module": "graph_nodes.architecture_correlation_node",
        "class": "ArchitectureCorrelationNode",
        "title": "Architecture Correlation",
    },
    "cross_service_correlation": {
        "module": "graph_nodes.cross_service_correlation_node",
        "class": "CrossServiceCorrelationNode",
        "title": "Cross-Service Correlation",
    },
    "correlation_engine": {
        "module": "graph_nodes.correlation_engine_node",
        "class": "CorrelationEngineNode",
        "title": "Correlation Engine",
    },
    "automated_followups": {
        "module": "graph_nodes.automated_followup_investigations_node",
        "class": "AutomatedFollowupInvestigationsNode",
        "title": "Automated Follow-up Investigations",
    },
    "dependency_chain_analysis": {
        "module": "graph_nodes.dependency_chain_analysis_node",
        "class": "DependencyChainAnalysisNode",
        "title": "Dependency Chain Analysis",
    },
    "infrastructure_impact": {
        "module": "graph_nodes.infrastructure_impact_assessment_node",
        "class": "InfrastructureImpactAssessmentNode",
        "title": "Infrastructure Impact Assessment",
    },
    "resource_utilization": {
        "module": "graph_nodes.resource_utilization_correlation_node",
        "class": "ResourceUtilizationCorrelationNode",
        "title": "Resource Utilization Correlation",
    },
    "evidence_aggregation": {
        "module": "graph_nodes.evidence_aggregation_node",
        "class": "EvidenceAggregationNode",
        "title": "Evidence Aggregation",
    },
    "real_time_stream_analysis": {
        "module": "graph_nodes.real_time_stream_analysis_node",
        "class": "RealTimeStreamAnalysisNode",
        "title": "Real-time Stream Analysis",
    },
    "predictive_analytics": {
        "module": "graph_nodes.predictive_analytics_node",
        "class": "PredictiveAnalyticsNode",
        "title": "Predictive Analytics",
    },
    "confidence_assessment": {
        "module": "graph_nodes.confidence_assessment_node",
        "class": "ConfidenceAssessmentNode",
        "title": "Confidence Assessment",
    },
    "confidence_decision_router": {
        "module": "graph_nodes.confidence_decision_router_node",
        "class": "ConfidenceDecisionRouterNode",
        "title": "Confidence Decision Router",
    },
    "generate_hypotheses": {
        "module": "graph_nodes.hypothesis_generation_node",
        "class": "HypothesisGenerationNode",
        "title": "Generate Hypotheses",
    },
    "additional_api_queries": {
        "module": "graph_nodes.additional_api_queries_node",
        "class": "AdditionalApiQueriesNode",
        "title": "Additional API Queries",
    },
    "targeted_clarification": {
        "module": "graph_nodes.targeted_clarification_node",
        "class": "TargetedClarificationNode",
        "title": "Targeted Clarification",
    },
    "root_cause_synthesis": {
        "module": "graph_nodes.root_cause_synthesis_node",
        "class": "RootCauseSynthesisNode",
        "title": "Root Cause Synthesis",
    },
    "timeline_reconstruction": {
        "module": "graph_nodes.timeline_reconstruction_node",
        "class": "TimelineReconstructionNode",
        "title": "Timeline Reconstruction",
    },
    "impact_analysis": {
        "module": "graph_nodes.impact_analysis_node",
        "class": "ImpactAnalysisNode",
        "title": "Impact Analysis",
    },
    "critical_path_identification": {
        "module": "graph_nodes.critical_path_identification_node",
        "class": "CriticalPathIdentificationNode",
        "title": "Critical Path Identification",
    },
    "cascade_failure_prediction": {
        "module": "graph_nodes.cascade_failure_prediction_node",
        "class": "CascadeFailurePredictionNode",
        "title": "Cascade Failure Prediction",
    },
    "evidence_compilation": {
        "module": "graph_nodes.evidence_compilation_node",
        "class": "EvidenceCompilationNode",
        "title": "Evidence Compilation",
    },
    "actionable_recommendations": {
        "module": "graph_nodes.actionable_recommendations_node",
        "class": "ActionableRecommendationsNode",
        "title": "Actionable Recommendations",
    },
    "recommendation_engine": {
        "module": "graph_nodes.recommendation_engine_node",
        "class": "RecommendationEngineNode",
        "title": "Recommendation Engine",
    },
    "automated_remediation": {
        "module": "graph_nodes.automated_remediation_node",
        "class": "AutomatedRemediationNode",
        "title": "Automated Remediation",
    },
    "response_formatting": {
        "module": "graph_nodes.response_formatting_node",
        "class": "ResponseFormattingNode",
        "title": "Response Formatting",
    },
    "context_memory_update": {
        "module": "graph_nodes.context_memory_update_node",
        "class": "ContextMemoryUpdateNode",
        "title": "Context Memory Update",
    },
    "context_manager": {
        "module": "graph_nodes.context_manager_node",
        "class": "ContextManagerNode",
        "title": "Context Manager",
    },
    "query_history": {
        "module": "graph_nodes.query_history_node",
        "class": "QueryHistoryNode",
        "title": "Query History",
    },
    "user_preferences": {
        "module": "graph_nodes.user_preferences_node",
        "class": "UserPreferencesNode",
        "title": "User Preferences",
    },
    "session_state": {
        "module": "graph_nodes.session_state_node",
        "class": "SessionStateNode",
        "title": "Session State",
    },
    "learning_repository": {
        "module": "graph_nodes.learning_repository_node",
        "class": "LearningRepositoryNode",
        "title": "Learning Repository",
    },
    "team_knowledge": {
        "module": "graph_nodes.team_knowledge_node",
        "class": "TeamKnowledgeNode",
        "title": "Team Knowledge",
    },
    "architecture_pattern_learning": {
        "module": "graph_nodes.architecture_pattern_learning_node",
        "class": "ArchitecturePatternLearningNode",
        "title": "Architecture Pattern Learning",
    },
    "cross_project_learning": {
        "module": "graph_nodes.cross_project_learning_node",
        "class": "CrossProjectLearningNode",
        "title": "Cross-Project Learning",
    },
    "present_results": {
        "module": "graph_nodes.present_results_node",
        "class": "PresentResultsNode",
        "title": "Present Results",
    },
    "user_satisfaction": {
        "module": "graph_nodes.user_satisfaction_node",
        "class": "UserSatisfactionNode",
        "title": "User Satisfaction",
    },
    "drill_down_investigation": {
        "module": "graph_nodes.drill_down_investigation_node",
        "class": "DrillDownInvestigationNode",
        "title": "Drill-Down Investigation",
    },
    "alternative_analysis_path": {
        "module": "graph_nodes.alternative_analysis_path_node",
        "class": "AlternativeAnalysisPathNode",
        "title": "Alternative Analysis Path",
    },
    "preventive_analysis": {
        "module": "graph_nodes.preventive_analysis_node",
        "class": "PreventiveAnalysisNode",
        "title": "Preventive Analysis",
    },
    "proactive_monitoring_setup": {
        "module": "graph_nodes.proactive_monitoring_setup_node",
        "class": "ProactiveMonitoringSetupNode",
        "title": "Proactive Monitoring Setup",
    },
    "session_complete": {
        "module": "graph_nodes.session_complete_node",
        "class": "SessionCompleteNode",
        "title": "Session Complete",
    },
}


def _import_node_class(module_path: str, class_name: str):
    """Import a node class using relative fallback to absolute paths."""

    try:
        module = importlib.import_module(f".{module_path}", package=__package__)
    except ImportError:
        module = importlib.import_module(f"app.services.agent.core.{module_path}")
    return getattr(module, class_name)


def _tool_result(state: Any, key: str) -> Dict[str, Any]:
    return (state.get("tool_results") or {}).get(key) or {}


# Lightweight summarizers let the frontend display concise node-level highlights.
NODE_SUMMARIZERS = {
    "user_query_input": lambda before, after: {
        "processed_question": after.get("processed_question"),
        "question": after.get("question"),
    },
    "architecture_loader": lambda before, after: {
        "context_summary": (after.get("architecture_context") or {}).get("context_summary"),
        "relevant_services": after.get("relevant_services"),
    },
    "architecture_loader_agent": lambda before, after: {
        "summary": after.get("architecture_agent_summary"),
    },
    "intent_and_query_analysis": lambda before, after: {
        "query_type": after.get("query_type"),
        "needs_clarification": after.get("needs_clarification"),
        "missing_info": after.get("missing_info"),
        "entities": after.get("extracted_entities"),
    },
    "query_classifier": lambda before, after: {
        "query_classifier_summary": after.get("query_classifier_summary"),
    },
    "direct_filter": lambda before, after: {
        "logging_filter": after.get("logging_filter"),
        "components": after.get("logging_filter_components"),
    },
    "single_stage_filter": lambda before, after: {
        "logging_filter": after.get("logging_filter"),
        "components": after.get("logging_filter_components"),
    },
    "architecture_query_decomposition": lambda before, after: {
        "anchors": len(((after.get("query_decomposition") or {}).get("anchors") or [])),
        "flow_hint": len(((after.get("query_decomposition") or {}).get("flow_hint") or [])),
    },
    "investigation_planner": lambda before, after: {
        "plan": after.get("investigation_planner_summary"),
    },
    "dependency_strategy": lambda before, after: {
        "plan": after.get("investigation_plan"),
    },
    "multi_stage_filter_planning": lambda before, after: {
        "filter_plan": after.get("filter_plan"),
    },
    "context_enhanced_filter_builder": lambda before, after: {
        "logging_filter": after.get("logging_filter"),
    },
    "filter_architect": lambda before, after: {
        "filter_architect_summary": after.get("filter_architect_summary"),
    },
    "context_aware_filter": lambda before, after: {
        "logging_filter": after.get("logging_filter"),
        "context_enrichment": after.get("context_enrichment"),
    },
    "filter_optimization": lambda before, after: {
        "logging_filter": after.get("logging_filter"),
        "order_by": after.get("order_by"),
        "optimization": after.get("logging_filter_optimization"),
    },
    "primary_call_prep": lambda before, after: {
        "request": after.get("logging_request"),
    },
    "api_orchestrator": lambda before, after: {
        "stats": after.get("api_orchestrator_stats"),
    },
    "execute_logging_api": lambda before, after: {
        **_tool_result(after, "logging_api"),
    },
    "performance_optimization": lambda before, after: {
        "optimization": after.get("performance_optimization_summary"),
    },
    "response_analysis": lambda before, after: {
        "result_quality": after.get("result_quality"),
        "result_stats": after.get("result_stats"),
    },
    "auto_refine_filters": lambda before, after: {
        "iterations": after.get("refinement_iterations"),
    },
    "broaden_search": lambda before, after: {
        "iterations": after.get("broadening_iterations"),
    },
    "arch_resource_discovery": lambda before, after: {
        "discovered": len(after.get("discovered_resources") or []),
    },
    "upstream_downstream_check": lambda before, after: {
        "checked": after.get("up_downstream_checked"),
    },
    "multi_dimensional_analysis": lambda before, after: {
        "summary": after.get("md_summary"),
    },
    "temporal_pattern_analysis": lambda before, after: {
        "temporal_trends": after.get("temporal_trends"),
    },
    "error_clustering": lambda before, after: {
        "clusters": after.get("error_clusters"),
    },
    "performance_metrics": lambda before, after: {
        "metrics": after.get("performance_metrics"),
    },
    "anomaly_detection": lambda before, after: {
        "anomalies": after.get("anomalies"),
    },
    "pattern_analyzer": lambda before, after: {
        "pattern_analyzer_summary": after.get("pattern_analyzer_summary"),
    },
    "ml_pattern_recognition": lambda before, after: {
        "ml_pattern_summary": after.get("ml_pattern_summary"),
    },
    "architecture_correlation": lambda before, after: {
        "finding_count": len(after.get("correlation_findings") or []),
    },
    "cross_service_correlation": lambda before, after: {
        "triggers": after.get("cross_service_triggers"),
    },
    "correlation_engine": lambda before, after: {
        "correlation_engine_summary": after.get("correlation_engine_summary"),
    },
    "automated_followups": lambda before, after: {
        "followups": after.get("auto_followup_investigations"),
    },
    "dependency_chain_analysis": lambda before, after: {
        "insights": after.get("dependency_chain_insights"),
    },
    "infrastructure_impact": lambda before, after: {
        "impact": after.get("infrastructure_impact_summary"),
    },
    "resource_utilization": lambda before, after: {
        "utilization": after.get("resource_utilization_summary"),
    },
    "evidence_aggregation": lambda before, after: {
        "evidence": after.get("evidence_summary"),
    },
    "real_time_stream_analysis": lambda before, after: {
        "stream": after.get("real_time_stream_summary"),
    },
    "predictive_analytics": lambda before, after: {
        "predictive": after.get("predictive_analytics_summary"),
    },
    "confidence_assessment": lambda before, after: {
        "confidence": after.get("investigation_confidence"),
    },
    "confidence_decision_router": lambda before, after: {
        "route": after.get("confidence_route"),
    },
    "generate_hypotheses": lambda before, after: {
        "hypotheses": after.get("hypotheses"),
    },
    "additional_api_queries": lambda before, after: {
        "tool": _tool_result(after, "additional_api_queries"),
    },
    "targeted_clarification": lambda before, after: {
        "questions": after.get("clarifying_questions"),
    },
    "wait_for_user_response": lambda before, after: {
        "pending_questions": after.get("clarifying_questions"),
        "missing_info": after.get("missing_info"),
        "waiting_since": after.get("last_clarification_prompt_at"),
        "needs_clarification": after.get("needs_clarification"),
    },
    "root_cause_synthesis": lambda before, after: {
        "synthesis": after.get("synthesis_summary"),
    },
    "timeline_reconstruction": lambda before, after: {
        "timeline": after.get("timeline_reconstruction"),
    },
    "impact_analysis": lambda before, after: {
        "impact": after.get("impact_analysis_summary"),
    },
    "critical_path_identification": lambda before, after: {
        "critical_path": after.get("critical_path_summary"),
    },
    "cascade_failure_prediction": lambda before, after: {
        "prediction": after.get("cascade_failure_risk"),
    },
    "evidence_compilation": lambda before, after: {
        "evidence_compilation": after.get("evidence_compilation"),
    },
    "actionable_recommendations": lambda before, after: {
        "actions": after.get("actions"),
    },
    "recommendation_engine": lambda before, after: {
        "recommendation_summary": after.get("recommendation_summary"),
    },
    "automated_remediation": lambda before, after: {
        "automated_remediation_summary": after.get("automated_remediation_summary"),
    },
    "response_formatting": lambda before, after: {
        "response": after.get("presentation"),
    },
    "context_memory_update": lambda before, after: {
        "context_memory": after.get("context_memory"),
    },
    "context_manager": lambda before, after: {
        "context_manager_snapshot": after.get("context_manager_snapshot"),
    },
    "query_history": lambda before, after: {
        "query_history": after.get("query_history"),
    },
    "user_preferences": lambda before, after: {
        "user_preferences": after.get("user_preferences"),
    },
    "session_state": lambda before, after: {
        "session_state": after.get("session_state"),
    },
    "learning_repository": lambda before, after: {
        "learning_repository": after.get("learning_repository"),
    },
    "team_knowledge": lambda before, after: {
        "team_knowledge": after.get("team_knowledge"),
    },
    "architecture_pattern_learning": lambda before, after: {
        "architecture_learning": after.get("architecture_learning"),
    },
    "cross_project_learning": lambda before, after: {
        "cross_project_learning_summary": after.get("cross_project_learning_summary"),
    },
    "present_results": lambda before, after: {
        "presentation": after.get("presentation"),
    },
    "user_satisfaction": lambda before, after: {
        "user_satisfaction": after.get("user_satisfaction"),
        "route": after.get("satisfaction_route"),
    },
    "drill_down_investigation": lambda before, after: {
        "drill_down": after.get("drill_down_plan"),
    },
    "alternative_analysis_path": lambda before, after: {
        "alternative_path": after.get("alternative_analysis_summary"),
    },
    "preventive_analysis": lambda before, after: {
        "preventive_actions": after.get("preventive_actions"),
    },
    "proactive_monitoring_setup": lambda before, after: {
        "proactive_monitoring_plan": after.get("proactive_monitoring_plan"),
    },
    "session_complete": lambda before, after: {
        "session_status": after.get("session_status"),
        "session_ready_at": after.get("session_ready_at"),
    },
}


# Start-payload builders shape the status event emitted when a node kicks off.
NODE_START_BUILDERS = {
    "user_query_input": lambda state: {
        "question_preview": (state.get("question") or "")[:120],
        "project_id": state.get("project_id"),
    },
    "architecture_loader": lambda state: {
        "project_id": state.get("project_id"),
    },
    "direct_filter": lambda state: {
        "services": state.get("services"),
    },
    "single_stage_filter": lambda state: {
        "has_filter": bool(state.get("logging_filter")),
    },
    "context_aware_filter": lambda state: {
        "has_arch_context": bool(state.get("architecture_context")),
    },
    "primary_call_prep": lambda state: {
        "project_id": state.get("project_id"),
        "limit": state.get("limit"),
    },
    "execute_logging_api": lambda state: {
        "request": state.get("logging_request"),
    },
    "response_analysis": lambda state: {
        "previous_quality": state.get("result_quality"),
    },
    "auto_refine_filters": lambda state: {
        "refinements": len(state.get("refinement_history") or []),
    },
    "broaden_search": lambda state: {
        "broadenings": state.get("broadening_iterations"),
    },
    "arch_resource_discovery": lambda state: {
        "previous_discoveries": len(state.get("discovered_resources") or []),
    },
    "multi_dimensional_analysis": lambda state: {
        "log_sample": len(state.get("relevant_logs") or []),
    },
    "confidence_assessment": lambda state: {
        "confidence": (state.get("investigation_confidence") or {}).get("score"),
    },
    "confidence_decision_router": lambda state: {
        "route_hint": state.get("confidence_route"),
    },
    "targeted_clarification": lambda state: {
        "pending_questions": len(state.get("clarifying_questions") or []),
    },
    "wait_for_user_response": lambda state: {
        "pending_questions": len(state.get("clarifying_questions") or []),
        "next_question": ((state.get("clarifying_questions") or [{}])[0]).get("question"),
        "missing_info": state.get("missing_info"),
    },
    "present_results": lambda state: {
        "existing_total": ((state.get("presentation") or {}).get("total")),
    },
    "user_satisfaction": lambda state: {
        "last_feedback": state.get("user_satisfaction"),
    },
}


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
        # Bypass repeated imports by caching instantiated node objects.
        self._node_cache: Dict[str, Any] = {}
        # Hold onto per-session snapshots captured at clarification pauses.
        self._waiting_states: Dict[str, Dict[str, Any]] = {}

        self._build_workflow()
        
        logger.info(f"GCPLogInvestigationAgent initialized with config: {self.config}")
    
    def _build_workflow(self) -> None:
        """Assemble the investigation graph with nodes grouped by investigation phase."""
        
        workflow = StateGraph(AgentState)
        
        # --- Intake & context bootstrapping ---------------------------------------------------
        user_query_node = UserQueryInputNode(self.config)
        architecture_loader_node = ArchitectureLoaderNode(self.config)
        architecture_loader_agent_node = ArchitectureLoaderAgentNode(self.config)
        intent_analysis_node = IntentAndQueryAnalysisNode(self.config)
        query_classifier_node = QueryClassifierNode(self.config)
        
        # --- Filter design & execution --------------------------------------------------------
        direct_filter_node = DirectFilterConstructionNode(self.config)
        single_stage_node = SingleStageFilterConstructionNode(self.config)
        context_aware_node = ContextAwareEnhancementNode(self.config)
        session_complete_node = SessionCompleteNode(self.config)
        filter_opt_node = FilterValidationOptimizationNode(self.config)
        primary_prep_node = PrimaryCallPreparationNode(self.config)
        api_orchestrator_node = APIOrchestratorNode(self.config)
        performance_optimization_node = PerformanceOptimizationNode(self.config)
        execute_api_node = ExecuteLoggingAPINode(self.config)
        
        # --- Result presentation & quality loops ---------------------------------------------
        present_results_node = PresentResultsNode(self.config)
        response_analysis_node = ResponseAnalysisNode(self.config)
        md_analysis_node = MultiDimensionalAnalysisNode(self.config)
        decompose_node = ArchitectureAwareQueryDecompositionNode(self.config)
        dependency_node = DependencyStrategyNode(self.config)
        investigation_planner_node = InvestigationPlannerNode(self.config)
        filter_planning_node = MultiStageFilterPlanningNode(self.config)
        filter_builder_node = ContextEnhancedFilterBuilderNode(self.config)
        filter_architect_node = FilterArchitectNode(self.config)
        auto_refine_node = AutoRefineFiltersNode(self.config)
        broaden_search_node = BroadenSearchNode(self.config)
        arch_discovery_node = ArchResourceDiscoveryNode(self.config)
        up_downstream_node = UpstreamDownstreamCheckNode(self.config)
        
        # Register each node with the graph so execution follows the investigation narrative.
        workflow.add_node("user_query_input", user_query_node.execute)
        workflow.add_node("architecture_loader", architecture_loader_node.execute)
        workflow.add_node("architecture_loader_agent", architecture_loader_agent_node.execute)
        workflow.add_node("intent_and_query_analysis", intent_analysis_node.execute)
        workflow.add_node("query_classifier", query_classifier_node.execute)
        workflow.add_node("direct_filter", direct_filter_node.execute)
        workflow.add_node("single_stage_filter", single_stage_node.execute)
        workflow.add_node("context_aware_filter", context_aware_node.execute)
        workflow.add_node("session_complete", session_complete_node.execute)
        workflow.add_node("filter_optimization", filter_opt_node.execute)
        workflow.add_node("primary_call_prep", primary_prep_node.execute)
        workflow.add_node("api_orchestrator", api_orchestrator_node.execute)
        workflow.add_node("performance_optimization", performance_optimization_node.execute)
        workflow.add_node("execute_logging_api", execute_api_node.execute)
        workflow.add_node("present_results", present_results_node.execute)
        workflow.add_node("response_analysis", response_analysis_node.execute)
        workflow.add_node("multi_dimensional_analysis", md_analysis_node.execute)
        # Downstream analytical nodes are registered later because they all fan out from phase five.
        workflow.add_node("architecture_query_decomposition", decompose_node.execute)
        workflow.add_node("investigation_planner", investigation_planner_node.execute)
        workflow.add_node("dependency_strategy", dependency_node.execute)
        workflow.add_node("multi_stage_filter_planning", filter_planning_node.execute)
        workflow.add_node("context_enhanced_filter_builder", filter_builder_node.execute)
        workflow.add_node("filter_architect", filter_architect_node.execute)
        workflow.add_node("auto_refine_filters", auto_refine_node.execute)
        workflow.add_node("broaden_search", broaden_search_node.execute)
        workflow.add_node("arch_resource_discovery", arch_discovery_node.execute)
        workflow.add_node("upstream_downstream_check", up_downstream_node.execute)
        
        workflow.set_entry_point("user_query_input")
        
        # Intake: capture the question, pull in architecture memory, then classify the problem space.
        workflow.add_edge("user_query_input", "architecture_loader")
        workflow.add_edge("architecture_loader", "architecture_loader_agent")
        workflow.add_edge("architecture_loader", "intent_and_query_analysis")
        workflow.add_edge("architecture_loader_agent", "intent_and_query_analysis")
        workflow.add_edge("intent_and_query_analysis", "query_classifier")

        # Decide whether we can proceed directly or need clarification / complex planning.
        #   proceed       -> Filters are ready; drop into the main construction path.
        #   clarification -> We need extra context before continuing; fan into the F/G/H nodes.
        #   complex       -> Query touches several dependent systems; run the architecture planner path.
        workflow.add_conditional_edges(
            "query_classifier",
            self._route_after_intent_analysis,
            {
                "proceed": "direct_filter",
                "clarification": "clarification_engine",
                "complex": "architecture_query_decomposition",
            }
        )
        # Complex branch: if the classifier tags the query as "complex", plan a multi-stage investigation.
        workflow.add_edge("architecture_query_decomposition", "investigation_planner")
        workflow.add_edge("investigation_planner", "dependency_strategy")
        workflow.add_edge("dependency_strategy", "multi_stage_filter_planning")
        workflow.add_edge("multi_stage_filter_planning", "context_enhanced_filter_builder")
        workflow.add_edge("context_enhanced_filter_builder", "filter_architect")
        workflow.add_edge("context_enhanced_filter_builder", "context_aware_filter")
        workflow.add_edge("filter_architect", "context_aware_filter")
        workflow.add_edge("direct_filter", "single_stage_filter")
        workflow.add_edge("single_stage_filter", "context_aware_filter")
        # Default branch: design the final filter, orchestrate API calls, and study the results.
        workflow.add_edge("context_aware_filter", "filter_optimization")
        workflow.add_edge("filter_optimization", "primary_call_prep")
        workflow.add_edge("primary_call_prep", "api_orchestrator")
        workflow.add_edge("primary_call_prep", "execute_logging_api")
        workflow.add_edge("api_orchestrator", "execute_logging_api")
        workflow.add_edge("execute_logging_api", "performance_optimization")
        workflow.add_edge("execute_logging_api", "response_analysis")
        workflow.add_edge("performance_optimization", "response_analysis")
        # Decide how to react to the returned dataset before continuing deeper analysis.
        #   too_many -> tighten filters until the dataset is manageable.
        #   too_few  -> widen the search criteria.
        #   empty    -> look for alternative resources / upstream signals.
        #   optimal  -> jump straight into advanced analytics.
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
        # Feed refinement loops back into filter construction until a useful slice of logs is produced.
        workflow.add_edge("auto_refine_filters", "context_aware_filter")
        workflow.add_edge("broaden_search", "context_aware_filter")
        workflow.add_edge("arch_resource_discovery", "upstream_downstream_check")
        workflow.add_edge("upstream_downstream_check", "context_aware_filter")
        
        # Clarification, in-depth analytics, and reporting fan out from the core result set.
        f_node = ClarificationEngineNode(self.config)
        g_node = ContextualQuestionGeneratorNode(self.config)
        h_node = WaitForUserResponseNode(self.config)
        ff_node = ArchitectureSpecificQuestionNode(self.config)
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
        real_time_node = RealTimeStreamAnalysisNode(self.config)
        predictive_node = PredictiveAnalyticsNode(self.config)
        z_node = ConfidenceAssessmentNode(self.config)
        aa_node = ConfidenceDecisionRouterNode(self.config)
        bb_node = HypothesisGenerationNode(self.config)
        cc_node = TargetedClarificationNode(self.config)
        dd_node = RootCauseSynthesisNode(self.config)
        ee_node = AdditionalApiQueriesNode(self.config)
        gg_node = TimelineReconstructionNode(self.config)
        hh_node = ImpactAnalysisNode(self.config)
        ii_node = CriticalPathIdentificationNode(self.config)
        jj_node = CascadeFailurePredictionNode(self.config)
        kk_node = EvidenceCompilationNode(self.config)
        ll_node = ActionableRecommendationsNode(self.config)
        mm_node = ResponseFormattingNode(self.config)
        nn_node = ContextMemoryUpdateNode(self.config)
        ccc_node = QueryHistoryNode(self.config)
        ddd_node = UserPreferencesNode(self.config)
        eee_node = SessionStateNode(self.config)
        fff_node = LearningRepositoryNode(self.config)
        ggg_node = TeamKnowledgeNode(self.config)
        oo_node = ArchitecturePatternLearningNode(self.config)
        cross_project_node = CrossProjectLearningNode(self.config)
        pattern_analyzer_node = PatternAnalyzerNode(self.config)
        ml_pattern_node = MLPatternRecognitionNode(self.config)
        correlation_engine_node = CorrelationEngineNode(self.config)
        synthesis_engine_node = SynthesisEngineNode(self.config)
        recommendation_engine_node = RecommendationEngineNode(self.config)
        automated_remediation_node = AutomatedRemediationNode(self.config)
        context_manager_node = ContextManagerNode(self.config)
        user_satisfaction_node = UserSatisfactionNode(self.config)
        drill_down_node = DrillDownInvestigationNode(self.config)
        alternative_path_node = AlternativeAnalysisPathNode(self.config)
        preventive_analysis_node = PreventiveAnalysisNode(self.config)
        proactive_monitoring_node = ProactiveMonitoringSetupNode(self.config)
        workflow.add_node("clarification_engine", f_node.execute)
        workflow.add_node("contextual_questions", g_node.execute)
        workflow.add_node("wait_for_user_response", h_node.execute)
        workflow.add_node("architecture_questions", ff_node.execute)
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
        workflow.add_node("real_time_stream_analysis", real_time_node.execute)
        workflow.add_node("predictive_analytics", predictive_node.execute)
        workflow.add_node("confidence_assessment", z_node.execute)
        workflow.add_node("confidence_decision_router", aa_node.execute)
        workflow.add_node("generate_hypotheses", bb_node.execute)
        workflow.add_node("targeted_clarification", cc_node.execute)
        workflow.add_node("root_cause_synthesis", dd_node.execute)
        workflow.add_node("additional_api_queries", ee_node.execute)
        workflow.add_node("timeline_reconstruction", gg_node.execute)
        workflow.add_node("impact_analysis", hh_node.execute)
        workflow.add_node("critical_path_identification", ii_node.execute)
        workflow.add_node("cascade_failure_prediction", jj_node.execute)
        workflow.add_node("evidence_compilation", kk_node.execute)
        workflow.add_node("actionable_recommendations", ll_node.execute)
        workflow.add_node("response_formatting", mm_node.execute)
        workflow.add_node("context_memory_update", nn_node.execute)
        workflow.add_node("query_history", ccc_node.execute)
        workflow.add_node("user_preferences", ddd_node.execute)
        workflow.add_node("session_state", eee_node.execute)
        workflow.add_node("learning_repository", fff_node.execute)
        workflow.add_node("team_knowledge", ggg_node.execute)
        workflow.add_node("architecture_pattern_learning", oo_node.execute)
        workflow.add_node("cross_project_learning", cross_project_node.execute)
        workflow.add_node("pattern_analyzer", pattern_analyzer_node.execute)
        workflow.add_node("ml_pattern_recognition", ml_pattern_node.execute)
        workflow.add_node("correlation_engine", correlation_engine_node.execute)
        workflow.add_node("synthesis_engine", synthesis_engine_node.execute)
        workflow.add_node("recommendation_engine", recommendation_engine_node.execute)
        workflow.add_node("automated_remediation", automated_remediation_node.execute)
        workflow.add_node("context_manager", context_manager_node.execute)
        workflow.add_node("user_satisfaction", user_satisfaction_node.execute)
        workflow.add_node("drill_down_investigation", drill_down_node.execute)
        workflow.add_node("alternative_analysis_path", alternative_path_node.execute)
        workflow.add_node("preventive_analysis", preventive_analysis_node.execute)
        workflow.add_node("proactive_monitoring_setup", proactive_monitoring_node.execute)
        workflow.add_edge("clarification_engine", "contextual_questions")
        workflow.add_edge("contextual_questions", "wait_for_user_response")
        workflow.add_edge("architecture_questions", "wait_for_user_response")
        # Closing the loop: once clarification arrives we restart at intake but with enriched state.
        workflow.add_edge("wait_for_user_response", "user_query_input")
        workflow.add_edge("multi_dimensional_analysis", "temporal_pattern_analysis")
        workflow.add_edge("multi_dimensional_analysis", "error_clustering")
        workflow.add_edge("multi_dimensional_analysis", "performance_metrics")
        workflow.add_edge("multi_dimensional_analysis", "anomaly_detection")
        workflow.add_edge("multi_dimensional_analysis", "pattern_analyzer")
        workflow.add_edge("multi_dimensional_analysis", "architecture_correlation")
        workflow.add_edge("pattern_analyzer", "architecture_correlation")
        workflow.add_edge("temporal_pattern_analysis", "cross_service_correlation")
        workflow.add_edge("error_clustering", "cross_service_correlation")
        workflow.add_edge("performance_metrics", "cross_service_correlation")
        workflow.add_edge("anomaly_detection", "ml_pattern_recognition")
        workflow.add_edge("anomaly_detection", "cross_service_correlation")
        workflow.add_edge("ml_pattern_recognition", "cross_service_correlation")
        workflow.add_edge("architecture_correlation", "cross_service_correlation")
        workflow.add_edge("cross_service_correlation", "correlation_engine")
        workflow.add_edge("cross_service_correlation", "automated_followups")
        workflow.add_edge("correlation_engine", "automated_followups")
        workflow.add_edge("automated_followups", "dependency_chain_analysis")
        workflow.add_edge("automated_followups", "infrastructure_impact")
        workflow.add_edge("automated_followups", "resource_utilization")
        workflow.add_edge("dependency_chain_analysis", "evidence_aggregation")
        workflow.add_edge("infrastructure_impact", "evidence_aggregation")
        workflow.add_edge("resource_utilization", "evidence_aggregation")
        workflow.add_edge("evidence_aggregation", "real_time_stream_analysis")
        workflow.add_edge("evidence_aggregation", "confidence_assessment")
        workflow.add_edge("real_time_stream_analysis", "predictive_analytics")
        workflow.add_edge("predictive_analytics", "confidence_assessment")
        workflow.add_edge("confidence_assessment", "confidence_decision_router")
        workflow.add_conditional_edges(
            "confidence_decision_router",
            self._route_after_confidence_decision,
            {
                "low": "generate_hypotheses",
                "medium": "targeted_clarification",
                "high": "root_cause_synthesis",
            }
        )
        # Low confidence: expand evidence via hypotheses, extra API calls, then re-check confidence.
        workflow.add_edge("generate_hypotheses", "additional_api_queries")
        workflow.add_edge("additional_api_queries", "evidence_aggregation")
        # Medium confidence: pause for clarification before re-entering intake with richer context.
        workflow.add_edge("targeted_clarification", "architecture_questions")
        # High confidence: drive toward narrative synthesis and impact assessment.
        workflow.add_edge("root_cause_synthesis", "synthesis_engine")
        workflow.add_edge("root_cause_synthesis", "timeline_reconstruction")
        workflow.add_edge("synthesis_engine", "timeline_reconstruction")
        workflow.add_edge("timeline_reconstruction", "impact_analysis")
        workflow.add_edge("impact_analysis", "critical_path_identification")
        workflow.add_edge("critical_path_identification", "cascade_failure_prediction")
        workflow.add_edge("cascade_failure_prediction", "evidence_compilation")
        workflow.add_edge("evidence_compilation", "actionable_recommendations")
        workflow.add_edge("actionable_recommendations", "response_formatting")
        workflow.add_edge("actionable_recommendations", "recommendation_engine")
        workflow.add_edge("recommendation_engine", "automated_remediation")
        workflow.add_edge("automated_remediation", "response_formatting")
        workflow.add_edge("response_formatting", "context_memory_update")
        # Once narrative output is ready, push artefacts into the long-lived memory subsystems.
        workflow.add_edge("context_memory_update", "architecture_pattern_learning")
        workflow.add_edge("context_memory_update", "context_manager")
        workflow.add_edge("context_memory_update", "query_history")
        workflow.add_edge("context_memory_update", "user_preferences")
        workflow.add_edge("context_memory_update", "session_state")
        workflow.add_edge("context_memory_update", "learning_repository")
        workflow.add_edge("context_memory_update", "team_knowledge")
        workflow.add_edge("context_manager", "architecture_pattern_learning")
        workflow.add_edge("query_history", "architecture_pattern_learning")
        workflow.add_edge("user_preferences", "architecture_pattern_learning")
        workflow.add_edge("session_state", "architecture_pattern_learning")
        workflow.add_edge("learning_repository", "architecture_pattern_learning")
        workflow.add_edge("team_knowledge", "architecture_pattern_learning")
        # Feed learnings back into reporting so insights include cross-run trends.
        workflow.add_edge("architecture_pattern_learning", "cross_project_learning")
        workflow.add_edge("architecture_pattern_learning", "present_results")
        workflow.add_edge("cross_project_learning", "present_results")
        workflow.add_conditional_edges(
            "user_satisfaction",
            self._route_after_user_satisfaction,
            {
                "satisfied": "session_complete",
                "drill_down": "drill_down_investigation",
                "alternative": "alternative_analysis_path",
                "preventive": "preventive_analysis",
            }
        )
        workflow.add_edge("present_results", "user_satisfaction")
        # Post-report branches loop back into earlier phases depending on the requested follow-up.
        workflow.add_edge("drill_down_investigation", "architecture_query_decomposition")
        workflow.add_edge("alternative_analysis_path", "intent_and_query_analysis")
        workflow.add_edge("preventive_analysis", "proactive_monitoring_setup")
        workflow.add_edge("proactive_monitoring_setup", "session_complete")
        workflow.add_edge("session_complete", END)
        
        # Finalise the graph so it can be executed by LangGraph at runtime.
        self.graph = workflow.compile()
        
        logger.info("LangGraph workflow built successfully")
    
    def _get_node_instance(self, node_key: str):
        if node_key not in NODE_SPECS:
            raise KeyError(f"Unknown workflow node '{node_key}'")
        if node_key not in self._node_cache:
            spec = NODE_SPECS[node_key]
            cls = _import_node_class(spec["module"], spec["class"])
            self._node_cache[node_key] = cls(self.config)
        return self._node_cache[node_key]

    def _get_node_title(self, node_key: str) -> str:
        spec = NODE_SPECS.get(node_key)
        if spec and spec.get("title"):
            return spec["title"]
        return node_key.replace("_", " ").title()

    def _store_waiting_state(self, session_id: Optional[str], state: AgentState) -> None:
        """Cache the workflow state while waiting on user clarification."""
        if not session_id:
            return
        try:
            execution_trace = list(state.get("_execution_trace") or [])
            resume_plan = {
                "mode": "pending",
                "silence_queue": execution_trace,
            }
            self._waiting_states[session_id] = {
                "state": copy.deepcopy(state),
                "stored_at": datetime.utcnow().isoformat(),
                "resume_plan": resume_plan,
            }
            logger.debug("Stored pending state for session %s", session_id)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to cache waiting state for session %s", session_id)

    def _pop_waiting_state(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Retrieve and clear cached state for a session if present."""
        if not session_id:
            return None
        return self._waiting_states.pop(session_id, None)

    def _mark_resume_plan(
        self,
        session_id: Optional[str],
        *,
        mode: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Annotate the cached state with resume metadata for the next turn."""

        if not session_id:
            return

        cached = self._waiting_states.get(session_id)
        if not cached:
            return

        resume_plan = cached.setdefault("resume_plan", {"mode": "pending", "silence_queue": []})
        silence_queue = list(resume_plan.get("silence_queue") or [])

        if mode == "clarification_followup":
            silence_queue = [
                node for node in silence_queue
                if node not in {"clarification_engine", "contextual_questions", "wait_for_user_response"}
            ]
        elif mode == "confidence_followup":
            silence_queue = [
                node for node in silence_queue
                if node not in {"targeted_clarification", "architecture_questions", "wait_for_user_response"}
            ]

        resume_plan["mode"] = mode
        resume_plan["silence_queue"] = silence_queue

        if metadata:
            resume_plan.update(metadata)

    def _prepare_state_for_resume(
        self,
        saved_context: Dict[str, Any],
        query_input: Dict[str, Any],
    ) -> AgentState:
        """Merge the saved state with the latest user clarification input."""

        raw_state = copy.deepcopy(saved_context.get("state") or {})
        if not raw_state:
            raise ValueError("Saved state payload is empty")

        session_id = query_input.get("session_id") or query_input.get("sessionId") or raw_state.get("session_id")
        raw_state["session_id"] = session_id

        now_iso = datetime.utcnow().isoformat()
        incoming_text = (query_input.get("question") or "").strip()
        original_question = raw_state.get("question", "")

        if incoming_text:
            # Preserve the original prompt while appending a timestamped clarification response.
            if original_question:
                combined = f"{original_question.strip()}\n\nClarification response ({now_iso}): {incoming_text}"
            else:
                combined = incoming_text
            raw_state["question"] = combined

        # Update base request parameters from the latest payload when supplied
        raw_state["project_id"] = query_input.get("project_id") or raw_state.get("project_id", "")
        for key in ("services", "time_range", "collection", "limit", "access_token", "user_id"):
            if query_input.get(key) is not None:
                raw_state[key] = query_input[key]

        # Reset clarification flags so the workflow can continue
        raw_state["needs_clarification"] = False
        raw_state["missing_info"] = []
        raw_state["error"] = None
        raw_state["current_step"] = "user_query_input"

        # Track clarification history and prune pending queue
        clarifying_questions = list(raw_state.get("clarifying_questions") or [])
        if clarifying_questions and incoming_text:
            answered_question = dict(clarifying_questions.pop(0))
            answered_question["answer"] = incoming_text
            answered_question["answered_at"] = now_iso
            history = list(raw_state.get("conversation_history") or [])
            if answered_question.get("question"):
                history.append({
                    "role": "assistant",
                    "content": answered_question.get("question"),
                    "timestamp": answered_question.get("created_at") or now_iso,
                    "metadata": {
                        "type": "clarifying_question",
                        "context": answered_question.get("context"),
                    },
                })
            history.append({
                "role": "user",
                "content": incoming_text,
                "timestamp": now_iso,
                "metadata": {
                    "type": "clarification_response",
                    "answered_question": answered_question.get("question"),
                },
            })
            raw_state["conversation_history"] = history

            clar_history = list(raw_state.get("clarification_responses") or [])
            clar_history.append({
                "question": answered_question.get("question"),
                "response": incoming_text,
                "responded_at": now_iso,
            })
            raw_state["clarification_responses"] = clar_history
        elif incoming_text:
            history = list(raw_state.get("conversation_history") or [])
            history.append({
                "role": "user",
                "content": incoming_text,
                "timestamp": now_iso,
                "metadata": {"type": "clarification_response"},
            })
            raw_state["conversation_history"] = history

        raw_state["clarifying_questions"] = clarifying_questions

        clar_context = dict(raw_state.get("clarification_context") or {})
        if incoming_text:
            clar_context["last_user_response"] = incoming_text
            clar_context["last_response_at"] = now_iso
        raw_state["clarification_context"] = clar_context

        analysis_lines = []
        if incoming_text:
            truncated = (incoming_text[:120] + "...") if len(incoming_text) > 120 else incoming_text
            analysis_lines = [
                "",
                "SECTION: Clarification Response",
                f"  - Received at: {now_iso}",
                f"  - User input: {truncated}",
            ]

        if analysis_lines:
            existing_analysis = raw_state.get("analysis") or ""
            raw_state["analysis"] = (existing_analysis + "\n" + "\n".join(analysis_lines)).strip()

        resume_plan = copy.deepcopy(saved_context.get("resume_plan") or {})
        raw_state["_resume_plan"] = resume_plan
        raw_state["resumed_from_wait"] = True
        raw_state["_execution_trace"] = []

        return cast(AgentState, raw_state)

    def _initialize_state(
        self,
        query_input: Dict[str, Any],
        session_id: Optional[str],
    ) -> Tuple[AgentState, bool, Dict[str, Any]]:
        """Create a fresh state or resume from a cached clarification checkpoint."""

        saved = self._pop_waiting_state(session_id)
        if saved:
            try:
                resume_plan = copy.deepcopy(saved.get("resume_plan") or {})
                resumed_state = self._prepare_state_for_resume(saved, query_input)
                resumed_state["_resume_plan"] = resume_plan
                logger.info("Resuming workflow from clarification checkpoint for session %s", session_id)
                return resumed_state, True, resume_plan
            except Exception:
                logger.exception("Failed to resume state for session %s; falling back to fresh state", session_id)

        # No cached state: build a pristine AgentState for a brand-new investigation turn.
        initial_state = self._create_initial_state(query_input, session_id)
        initial_state["_resume_plan"] = {}
        return initial_state, False, {}

    def _summarize_node(self, node_key: str, before: AgentState, after: AgentState) -> Dict[str, Any]:
        summarizer = NODE_SUMMARIZERS.get(node_key)
        if summarizer:
            with suppress(Exception):
                data = summarizer(before, after)
                if data is not None:
                    return data
        return {}

    def _make_node_event(
        self,
        node_key: str,
        title: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "type": "node_event",
            "node": node_key,
            "title": title,
            "status": status,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

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
        """Legacy hook retained for completeness (currently unused)."""
        if state.get("needs_clarification", False):
            return "clarification"
        return "intent_classification"

    def _route_after_confidence_decision(self, state: AgentState) -> str:
        """Translate the confidence router score into the next investigation branch."""
        route = str(state.get("confidence_route") or "medium").lower()
        if route in {"low", "medium", "high"}:
            return route
        return "medium"

    def _route_after_intent_analysis(self, state: AgentState) -> str:
        """Map the initial classifier output to one of three major entry routes."""
        if state.get("needs_clarification", False):
            return "clarification"
        qt = (state.get("query_type") or "").strip().lower()
        if qt == "complex":
            return "complex"
        if qt == "ambiguous":
            return "clarification"
        return "proceed"

    def _route_after_response_analysis(self, state: AgentState) -> str:
        """Interpret the response quality heuristic into the refinement loop destination."""
        q = state.get("result_quality")
        if q in {"too_many", "too_few", "empty", "optimal"}:
            return q
        # Default to optimal if unspecified (defensive; R should always set it)
        return "optimal"

    def _route_after_user_satisfaction(self, state: AgentState) -> str:
        """Resolve post-report actions based on explicit or inferred user feedback."""
        route = str(state.get("satisfaction_route") or state.get("user_satisfaction") or "satisfied").lower()
        if route in {"satisfied", "drill_down", "alternative", "preventive"}:
            return route
        return "satisfied"
    
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
            
            # Initialize state from input or resume from pending clarification
            initial_state, resumed_from_wait, _ = self._initialize_state(query_input, session_id)
            if resumed_from_wait:
                logger.debug("Resuming workflow for session %s after clarification", session_id)
            
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

            state, resumed_from_wait, resume_plan = self._initialize_state(query_input, session_id)
            if resumed_from_wait:
                logger.debug("Resuming streaming workflow for session %s after clarification", session_id)

            execution_trace: List[str] = []
            state["_execution_trace"] = execution_trace
            silence_queue = deque((resume_plan or {}).get("silence_queue") or [])
            resume_mode = (resume_plan or {}).get("mode")

            if resumed_from_wait:
                state["resumed_from_wait"] = True
                yield {
                    "type": "status",
                    "message": "Resuming investigation from pending checkpoint",
                    "data": {
                        "resume_mode": resume_mode or "unknown",
                        "session_id": state.get("session_id"),
                    },
                }

            async def run_node(node_key: str, *, start_data: Optional[Dict[str, Any]] = None):
                nonlocal state
                emit_events = True
                if silence_queue and silence_queue[0] == node_key:
                    silence_queue.popleft()
                    emit_events = False
                title = self._get_node_title(node_key)
                payload = start_data
                if payload is None:
                    builder = NODE_START_BUILDERS.get(node_key)
                    if builder:
                        with suppress(Exception):
                            built = builder(state)
                            if built:
                                payload = built
                if emit_events:
                    yield self._make_node_event(node_key, title, "started", payload or {})

                before_state = dict(state)
                node_instance = self._get_node_instance(node_key)
                try:
                    new_state = await node_instance.execute(state)
                except Exception as exc:  # pragma: no cover - defensive
                    err_data = {"message": str(exc)}
                    yield self._make_node_event(node_key, title, "error", err_data)
                    copy_state = state.copy()
                    copy_state["error"] = str(exc)
                    state = copy_state
                    raise

                summary = self._summarize_node(node_key, before_state, new_state)
                state = new_state
                execution_trace.append(node_key)
                state["_execution_trace"] = execution_trace
                if node_key == "wait_for_user_response":
                    # Snapshot the clarifying state so the follow-up message can resume the graph.
                    self._store_waiting_state(state.get("session_id"), state)
                if emit_events:
                    yield self._make_node_event(node_key, title, "completed", summary or {})

            async def run_nodes(node_keys):
                for key in node_keys:
                    async for evt in run_node(key):
                        yield evt

            def emit(node_key: str, status: str, data: Optional[Dict[str, Any]] = None):
                return self._make_node_event(node_key, self._get_node_title(node_key), status, data or {})

            # Intake sequence: capture the question, load context, and classify intent.
            async for evt in run_nodes([
                "user_query_input",
                "architecture_loader",
                "architecture_loader_agent",
                "intent_and_query_analysis",
                "query_classifier",
            ]):
                yield evt

            intent_route = self._route_after_intent_analysis(state)
            if intent_route == "clarification":
                async for evt in run_nodes([
                    "clarification_engine",
                    "contextual_questions",
                    "wait_for_user_response",
                ]):
                    yield evt

                self._mark_resume_plan(state.get("session_id"), mode="clarification_followup")

                response = self._format_response(state)
                yield {"type": "result", "data": response}
                logger.info("Streaming query processing completed with clarification request")
                return

            if intent_route == "complex":
                async for evt in run_nodes([
                    "architecture_query_decomposition",
                    "investigation_planner",
                    "dependency_strategy",
                    "multi_stage_filter_planning",
                    "context_enhanced_filter_builder",
                    "filter_architect",
                ]):
                    yield evt
            else:
                async for evt in run_nodes([
                    "direct_filter",
                    "single_stage_filter",
                ]):
                    yield evt

            async for evt in run_nodes([
                "context_aware_filter",
                "filter_optimization",
                "primary_call_prep",
                "api_orchestrator",
                "execute_logging_api",
                "performance_optimization",
                "response_analysis",
            ]):
                yield evt

            loop_guard = 0
            max_loops = 4
            max_refinements = 2
            max_broadens = 1
            max_arch = 1
            refinement_iters = 0
            broaden_iters = 0
            arch_iters = 0

            while loop_guard < max_loops:
                outcome = self._route_after_response_analysis(state)
                if outcome == "optimal":
                    break

                loop_guard += 1
                performed = False

                if outcome == "too_many" and refinement_iters < max_refinements:
                    async for evt in run_node("auto_refine_filters"):
                        yield evt
                    refinement_iters += 1
                    performed = True
                elif outcome == "too_few" and broaden_iters < max_broadens:
                    async for evt in run_node("broaden_search"):
                        yield evt
                    broaden_iters += 1
                    performed = True
                elif outcome == "empty" and arch_iters < max_arch:
                    async for evt in run_node("arch_resource_discovery"):
                        yield evt
                    async for evt in run_node("upstream_downstream_check"):
                        yield evt
                    arch_iters += 1
                    performed = True
                else:
                    note = {
                        "note": "Max refinements reached; proceeding with current results",
                        "outcome": outcome,
                    }
                    yield emit("response_analysis", "completed", note)
                    break

                if performed:
                    async for evt in run_nodes([
                        "context_aware_filter",
                        "filter_optimization",
                        "primary_call_prep",
                        "api_orchestrator",
                        "execute_logging_api",
                        "performance_optimization",
                        "response_analysis",
                    ]):
                        yield evt

            phase5_nodes = [
                "multi_dimensional_analysis",
                "temporal_pattern_analysis",
                "error_clustering",
                "performance_metrics",
                "anomaly_detection",
                "pattern_analyzer",
                "ml_pattern_recognition",
                "architecture_correlation",
                "cross_service_correlation",
                "correlation_engine",
                "automated_followups",
                "dependency_chain_analysis",
                "infrastructure_impact",
                "resource_utilization",
                "evidence_aggregation",
                "real_time_stream_analysis",
                "predictive_analytics",
                "confidence_assessment",
            ]

            async for evt in run_nodes(phase5_nodes):
                yield evt

            async for evt in run_node("confidence_decision_router"):
                yield evt

            decision = self._route_after_confidence_decision(state)
            low_handled = False

            while True:
                # Iterate until confidence stabilises: try to recover low confidence once, then
                # either ask the user for help (medium) or proceed to high-confidence synthesis.
                if decision == "low" and not low_handled:
                    async for evt in run_nodes([
                        "generate_hypotheses",
                        "additional_api_queries",
                        "evidence_aggregation",
                        "predictive_analytics",
                        "confidence_assessment",
                        "confidence_decision_router",
                    ]):
                        yield evt
                    decision = self._route_after_confidence_decision(state)
                    low_handled = True
                    continue

                if decision == "medium":
                    async for evt in run_nodes([
                        "targeted_clarification",
                        "architecture_questions",
                        "wait_for_user_response",
                    ]):
                        yield evt
                    self._mark_resume_plan(state.get("session_id"), mode="confidence_followup")
                    response = self._format_response(state)
                    yield {"type": "result", "data": response}
                    logger.info("Streaming query completed with targeted clarification route")
                    return

                async for evt in run_nodes([
                    "root_cause_synthesis",
                    "timeline_reconstruction",
                    "impact_analysis",
                    "critical_path_identification",
                    "cascade_failure_prediction",
                    "evidence_compilation",
                ]):
                    yield evt
                break

            async for evt in run_nodes([
                "actionable_recommendations",
                "recommendation_engine",
                "automated_remediation",
                "response_formatting",
                "context_memory_update",
                "context_manager",
                "query_history",
                "user_preferences",
                "session_state",
                "learning_repository",
                "team_knowledge",
                "architecture_pattern_learning",
                "cross_project_learning",
                "present_results",
                "user_satisfaction",
            ]):
                yield evt

            satisfaction = self._route_after_user_satisfaction(state)
            if satisfaction == "drill_down":
                async for evt in run_node("drill_down_investigation"):
                    yield evt
            elif satisfaction == "alternative":
                async for evt in run_node("alternative_analysis_path"):
                    yield evt
            elif satisfaction == "preventive":
                async for evt in run_nodes([
                    "preventive_analysis",
                    "proactive_monitoring_setup",
                ]):
                    yield evt

            async for evt in run_node("session_complete"):
                yield evt

            analysis = state.get("analysis", "")
            if analysis:
                words = analysis.split()
                chunk_size = 5
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = " ".join(chunk_words)
                    if i + chunk_size < len(words):
                        chunk_text += " "
                    yield {"type": "chunk", "content": chunk_text, "message": chunk_text}
                    await asyncio.sleep(0.03)

            response = self._format_response(state)
            yield {"type": "result", "data": response}
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
            clarification_responses=[],

            # Conversation management
            conversation_history=[],
            context_summary="",
            error=None,
            resumed_from_wait=False,
            _execution_trace=[],
            _resume_plan={},
            
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
            user_preferences_summary={},
            architecture_insights={},
            
            # Architecture context (for A1 node)
            architecture_context=None,
            relevant_services=None,

            # Defaults for long-running context management structures captured near the end of the workflow.
            context_memory={},
            query_history=[],
            query_history_stats={},
            session_state={},
            session_state_snapshot=None,
            learning_repository=[],
            learning_repository_summary={},
            team_knowledge=[],
            team_knowledge_stats={},
            architecture_learning=[],
            architecture_learning_meta={},
            investigation_confidence={"score": 0.0, "level": "low"},
            result_quality=None,
            user_feedback={},
            user_satisfaction=None,
            satisfaction_route=None,
            drill_down_requested=False,
            alternative_path_requested=False,
            preventive_actions=[],
            proactive_monitoring_plan={},
            user_feedback_history=[],
            architecture_agent_summary={},
            query_classifier_summary={},
            investigation_planner_summary={},
            filter_architect_summary={},
            api_orchestrator_stats={},
            correlation_engine_summary={},
            pattern_analyzer_summary={},
            synthesis_summary={},
            recommendation_summary={},
            context_manager_snapshot={},
            real_time_stream_summary={},
            predictive_analytics_summary={},
            ml_pattern_summary={},
            cross_project_learning_summary={},
            automated_remediation_summary={},
            performance_optimization_summary={},
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
            "resumed_from_wait": final_state.get("resumed_from_wait", False),
            "resume_mode": (final_state.get("_resume_plan") or {}).get("mode"),
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
