# Phase 1: Core Agent Infrastructure - Detailed Implementation Plan

## Overview
This document provides detailed implementation guidance for Phase 1 of the Advanced Log Analysis Agent. Phase 1 focuses on establishing the foundational LangGraph agent structure with basic state management and workflow routing.

## Phase 1 Goals
- ✅ Establish comprehensive AgentState management
- ✅ Create basic LangGraph workflow structure
- ✅ Implement essential agent nodes
- ✅ Build basic query processing capabilities
- ✅ Set up state persistence and session management

## Detailed Task Breakdown

### Task 1.1: State Management System

#### Task 1.1.1: Design and Implement AgentState Class
**File**: `backend/app/services/agent/core/state.py`

**Requirements**:
- Comprehensive state tracking for all agent operations
- Type safety with TypedDict
- Support for complex nested data structures
- Extensible design for future enhancements

**Implementation**:
```python
from typing import TypedDict, Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class QueryComplexity(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    AMBIGUOUS = "ambiguous"

class InvestigationStatus(Enum):
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    CLARIFYING = "clarifying"
    INVESTIGATING = "investigating"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    ERROR = "error"

class AgentState(TypedDict):
    # === User Inputs ===
    question: str
    project_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    services: Optional[List[str]]
    time_range: Optional[Dict[str, str]]
    collection: Optional[str]
    limit: int
    access_token: Optional[str]
    
    # === Query Analysis ===
    query_complexity: Optional[QueryComplexity]
    intent_classification: Optional[Dict[str, Any]]
    entities_extracted: Optional[List[Dict[str, Any]]]
    missing_parameters: Optional[List[str]]
    needs_clarification: bool
    clarification_questions: Optional[List[Dict[str, str]]]
    
    # === Investigation Context ===
    investigation_status: InvestigationStatus
    current_step: str
    investigation_context: Dict[str, Any]
    architecture_context: Optional[Dict[str, Any]]
    investigation_history: List[Dict[str, Any]]
    
    # === Results and Analysis ===
    analysis: Optional[str]
    relevant_logs: Optional[List[Dict[str, Any]]]
    root_cause: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[float]
    
    # === Memory and Learning ===
    conversation_history: List[Dict[str, Any]]
    learned_patterns: Dict[str, Any]
    user_preferences: Dict[str, Any]
    session_context: Dict[str, Any]
    
    # === Error Handling ===
    error: Optional[str]
    retry_count: int
    last_error_time: Optional[datetime]
    
    # === Performance Tracking ===
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    processing_time: Optional[float]
    api_calls_made: int
    filters_applied: List[Dict[str, Any]]
```

#### Task 1.1.2: Create State Persistence Layer
**File**: `backend/app/services/agent/core/persistence.py`

**Requirements**:
- Redis-based state storage for production
- Memory-based fallback for development
- State serialization/deserialization
- Session management and cleanup
- State versioning and migration

**Implementation**:
```python
import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

class StatePersistence:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_store = {}
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except Exception as e:
                logging.warning(f"Redis connection failed: {e}, using memory store")
    
    async def save_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save agent state to persistent storage"""
        try:
            # Serialize state
            serialized_state = self._serialize_state(state)
            
            if self.redis_client:
                # Save to Redis with TTL
                self.redis_client.setex(
                    f"agent_state:{session_id}",
                    timedelta(hours=24),
                    serialized_state
                )
            else:
                # Save to memory store
                self.memory_store[session_id] = {
                    'state': serialized_state,
                    'timestamp': datetime.now()
                }
            
            return True
        except Exception as e:
            logging.error(f"Failed to save state: {e}")
            return False
    
    async def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state from persistent storage"""
        try:
            if self.redis_client:
                serialized_state = self.redis_client.get(f"agent_state:{session_id}")
                if serialized_state:
                    return self._deserialize_state(serialized_state)
            else:
                if session_id in self.memory_store:
                    return self._deserialize_state(
                        self.memory_store[session_id]['state']
                    )
            
            return None
        except Exception as e:
            logging.error(f"Failed to load state: {e}")
            return None
    
    def _serialize_state(self, state: Dict[str, Any]) -> str:
        """Serialize state to JSON string"""
        return json.dumps(state, default=str)
    
    def _deserialize_state(self, serialized_state: str) -> Dict[str, Any]:
        """Deserialize state from JSON string"""
        return json.loads(serialized_state)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        # Implementation for cleanup logic
        pass
```

### Task 1.2: Core LangGraph Workflow

#### Task 1.2.1: Implement Basic Workflow Graph Structure
**File**: `backend/app/services/agent/core/workflow.py`

**Requirements**:
- LangGraph workflow definition
- Node connections and routing
- Conditional edge logic
- Error handling and recovery

**Implementation**:
```python
from langgraph.graph import StateGraph, END
from typing import Dict, Any, Literal
from .state import AgentState
from .nodes import (
    InputAnalyzer,
    QueryClassifier,
    ContextLoader,
    FilterBuilder,
    LogRetriever,
    LogAnalyzer,
    ResponseFormatter,
    StateManager
)

class AgentWorkflow:
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("input_analyzer", InputAnalyzer())
        workflow.add_node("query_classifier", QueryClassifier())
        workflow.add_node("context_loader", ContextLoader())
        workflow.add_node("filter_builder", FilterBuilder())
        workflow.add_node("log_retriever", LogRetriever())
        workflow.add_node("log_analyzer", LogAnalyzer())
        workflow.add_node("response_formatter", ResponseFormatter())
        workflow.add_node("state_manager", StateManager())
        
        # Set entry point
        workflow.set_entry_point("input_analyzer")
        
        # Add edges
        workflow.add_edge("input_analyzer", "query_classifier")
        workflow.add_edge("query_classifier", "context_loader")
        workflow.add_edge("context_loader", "filter_builder")
        workflow.add_edge("filter_builder", "log_retriever")
        workflow.add_edge("log_retriever", "log_analyzer")
        workflow.add_edge("log_analyzer", "response_formatter")
        workflow.add_edge("response_formatter", "state_manager")
        workflow.add_edge("state_manager", END)
        
        # Add conditional edges for clarification
        workflow.add_conditional_edges(
            "query_classifier",
            self._should_clarify,
            {
                "clarify": "response_formatter",
                "proceed": "context_loader"
            }
        )
        
        return workflow.compile()
    
    def _should_clarify(self, state: AgentState) -> Literal["clarify", "proceed"]:
        """Determine if clarification is needed"""
        if state.get("needs_clarification", False):
            return "clarify"
        return "proceed"
    
    async def execute(self, initial_state: AgentState) -> AgentState:
        """Execute the workflow with given initial state"""
        return await self.workflow.ainvoke(initial_state)
```

#### Task 1.2.2: Create Essential Agent Nodes
**File**: `backend/app/services/agent/core/nodes.py`

**Requirements**:
- Implement all core agent nodes
- Consistent error handling
- State validation
- Logging and monitoring

**Implementation**:
```python
from typing import Dict, Any
import logging
from .state import AgentState, QueryComplexity, InvestigationStatus

class BaseNode:
    """Base class for all agent nodes"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute the node logic"""
        try:
            self.logger.info(f"Executing {self.__class__.__name__}")
            return self._execute(state)
        except Exception as e:
            self.logger.error(f"Error in {self.__class__.__name__}: {e}")
            return self._handle_error(state, e)
    
    def _execute(self, state: AgentState) -> AgentState:
        """Override in subclasses"""
        raise NotImplementedError
    
    def _handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Handle errors gracefully"""
        state["error"] = str(error)
        state["investigation_status"] = InvestigationStatus.ERROR
        return state

class InputAnalyzer(BaseNode):
    """Analyze user input and extract basic information"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Basic input validation
        if not state.get("question"):
            state["error"] = "No question provided"
            return state
        
        # Extract basic information
        question = state["question"].strip()
        state["question"] = question
        
        # Initialize investigation context
        state["investigation_context"] = {
            "original_question": question,
            "analysis_start_time": datetime.now().isoformat(),
            "steps_completed": []
        }
        
        state["investigation_status"] = InvestigationStatus.INITIALIZING
        state["current_step"] = "input_analysis"
        
        return state

class QueryClassifier(BaseNode):
    """Classify query type and complexity"""
    
    def _execute(self, state: AgentState) -> AgentState:
        question = state["question"].lower()
        
        # Simple heuristics for query classification
        complexity = self._classify_complexity(question)
        state["query_complexity"] = complexity
        
        # Extract entities (basic implementation)
        entities = self._extract_entities(question)
        state["entities_extracted"] = entities
        
        # Check for missing parameters
        missing_params = self._check_missing_parameters(state)
        state["missing_parameters"] = missing_params
        state["needs_clarification"] = len(missing_params) > 0
        
        if state["needs_clarification"]:
            state["clarification_questions"] = self._generate_clarification_questions(missing_params)
        
        state["current_step"] = "query_classification"
        return state
    
    def _classify_complexity(self, question: str) -> QueryComplexity:
        """Classify query complexity"""
        complex_indicators = ["analyze", "investigate", "root cause", "correlation", "pattern"]
        ambiguous_indicators = ["?", "help", "what", "how", "why"]
        
        if any(indicator in question for indicator in complex_indicators):
            return QueryComplexity.COMPLEX
        elif any(indicator in question for indicator in ambiguous_indicators):
            return QueryComplexity.AMBIGUOUS
        else:
            return QueryComplexity.SIMPLE
    
    def _extract_entities(self, question: str) -> List[Dict[str, Any]]:
        """Extract entities from question (basic implementation)"""
        entities = []
        
        # Look for service names
        service_keywords = ["service", "api", "endpoint", "function"]
        for keyword in service_keywords:
            if keyword in question:
                entities.append({
                    "type": "service",
                    "value": keyword,
                    "confidence": 0.7
                })
        
        return entities
    
    def _check_missing_parameters(self, state: AgentState) -> List[str]:
        """Check for missing required parameters"""
        missing = []
        
        if not state.get("project_id"):
            missing.append("project_id")
        
        if not state.get("time_range"):
            missing.append("time_range")
        
        return missing
    
    def _generate_clarification_questions(self, missing_params: List[str]) -> List[Dict[str, str]]:
        """Generate clarification questions for missing parameters"""
        questions = []
        
        for param in missing_params:
            if param == "project_id":
                questions.append({
                    "parameter": "project_id",
                    "question": "Which GCP project would you like to analyze?",
                    "type": "project_selection"
                })
            elif param == "time_range":
                questions.append({
                    "parameter": "time_range",
                    "question": "What time range would you like to investigate?",
                    "type": "time_range_selection"
                })
        
        return questions

class ContextLoader(BaseNode):
    """Load project and session context"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Load project context (placeholder implementation)
        project_id = state.get("project_id")
        if project_id:
            state["architecture_context"] = {
                "project_id": project_id,
                "services": state.get("services", []),
                "loaded_at": datetime.now().isoformat()
            }
        
        # Load session context
        session_id = state.get("session_id")
        if session_id:
            # Load previous conversation history
            state["conversation_history"] = self._load_conversation_history(session_id)
        
        state["current_step"] = "context_loading"
        return state
    
    def _load_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Load conversation history for session"""
        # Placeholder implementation
        return []

class FilterBuilder(BaseNode):
    """Build GCP Logging API filters"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Build basic filter
        filters = self._build_filters(state)
        state["filters_applied"] = filters
        
        state["current_step"] = "filter_building"
        return state
    
    def _build_filters(self, state: AgentState) -> List[Dict[str, Any]]:
        """Build GCP Logging API filters"""
        filters = []
        
        # Project filter
        if state.get("project_id"):
            filters.append({
                "type": "project",
                "value": f"projects/{state['project_id']}"
            })
        
        # Time range filter
        if state.get("time_range"):
            time_range = state["time_range"]
            filters.append({
                "type": "timestamp",
                "value": f"timestamp>=\"{time_range.get('start')}\" AND timestamp<=\"{time_range.get('end')}\""
            })
        
        # Service filter
        if state.get("services"):
            services = state["services"]
            service_filter = " OR ".join([f"resource.labels.service_name=\"{service}\"" for service in services])
            filters.append({
                "type": "service",
                "value": service_filter
            })
        
        return filters

class LogRetriever(BaseNode):
    """Retrieve logs from GCP Logging API"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Placeholder for log retrieval
        # This will integrate with existing GCP Logging API
        state["relevant_logs"] = []
        state["current_step"] = "log_retrieval"
        return state

class LogAnalyzer(BaseNode):
    """Analyze retrieved logs"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Placeholder for log analysis
        state["analysis"] = "Log analysis completed"
        state["current_step"] = "log_analysis"
        return state

class ResponseFormatter(BaseNode):
    """Format response for user"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Format response based on current state
        if state.get("needs_clarification"):
            state["response"] = self._format_clarification_response(state)
        else:
            state["response"] = self._format_analysis_response(state)
        
        state["current_step"] = "response_formatting"
        return state
    
    def _format_clarification_response(self, state: AgentState) -> Dict[str, Any]:
        """Format clarification response"""
        return {
            "type": "clarification",
            "message": "I need some additional information to help you effectively.",
            "questions": state.get("clarification_questions", []),
            "missing_parameters": state.get("missing_parameters", [])
        }
    
    def _format_analysis_response(self, state: AgentState) -> Dict[str, Any]:
        """Format analysis response"""
        return {
            "type": "analysis",
            "analysis": state.get("analysis", ""),
            "logs": state.get("relevant_logs", []),
            "recommendations": state.get("recommendations", [])
        }

class StateManager(BaseNode):
    """Manage state persistence and updates"""
    
    def _execute(self, state: AgentState) -> AgentState:
        # Update investigation history
        if "investigation_history" not in state:
            state["investigation_history"] = []
        
        state["investigation_history"].append({
            "step": state["current_step"],
            "timestamp": datetime.now().isoformat(),
            "status": state.get("investigation_status", InvestigationStatus.INITIALIZING)
        })
        
        # Update conversation history
        if "conversation_history" not in state:
            state["conversation_history"] = []
        
        state["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_question": state.get("question", ""),
            "agent_response": state.get("response", {}),
            "step": state["current_step"]
        })
        
        state["current_step"] = "state_management"
        return state
```

### Task 1.3: Basic Query Processing

#### Task 1.3.1: Implement Query Intent Classification
**File**: `backend/app/services/agent/intelligence/query_classifier.py`

**Requirements**:
- Natural language understanding
- Intent classification
- Entity extraction
- Confidence scoring

#### Task 1.3.2: Create Basic Filter Construction
**File**: `backend/app/services/agent/filters/filter_builder.py`

**Requirements**:
- GCP Logging API filter generation
- Parameter validation
- Filter optimization
- Error handling

## Testing Strategy

### Unit Tests
- Test each node individually
- Mock external dependencies
- Validate state transitions
- Test error handling

### Integration Tests
- Test complete workflow execution
- Test state persistence
- Test API integration
- Test error recovery

### End-to-End Tests
- Test complete user scenarios
- Test clarification flow
- Test analysis flow
- Test performance

## Success Criteria

### Functional Requirements
- ✅ AgentState class implemented with all required fields
- ✅ Basic LangGraph workflow structure created
- ✅ All essential nodes implemented
- ✅ State persistence working
- ✅ Basic query processing functional

### Performance Requirements
- Response time < 2 seconds for simple queries
- Memory usage < 100MB per session
- Error rate < 1%
- State persistence success rate > 99%

### Quality Requirements
- Code coverage > 80%
- All tests passing
- No critical security vulnerabilities
- Documentation complete

## Next Steps

1. **Immediate Actions**:
   - Create the file structure for Phase 1
   - Implement AgentState class
   - Set up basic LangGraph workflow
   - Create essential nodes

2. **Week 1 Completion**:
   - All core infrastructure implemented
   - Basic testing framework in place
   - Initial integration with existing GCP API

3. **Week 2 Completion**:
   - State persistence working
   - Basic query processing functional
   - Integration tests passing
   - Ready for Phase 2

This detailed plan provides the foundation for implementing Phase 1 of the Advanced Log Analysis Agent. Each task includes specific requirements, implementation guidance, and success criteria to ensure a solid foundation for the more advanced features in subsequent phases.
