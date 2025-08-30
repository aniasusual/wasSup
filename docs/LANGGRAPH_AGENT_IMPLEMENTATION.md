# LangGraph Agent Implementation

## Overview

This document explains the implementation of a LangGraph-based agent system that replaces the previous monolithic LLM agent. The new system provides a state-driven, multi-node workflow for log investigation and analysis.

## What is LangGraph?

LangGraph is a framework for building stateful, multi-step AI applications using LangChain. It enables:

- **State Management**: Persistent state objects that track conversation context, investigation progress, and user preferences
- **Node-based Workflow**: Structured execution through a graph of specialized nodes
- **Conditional Routing**: Dynamic decision-making based on current state and user input
- **Tool Integration**: Seamless integration with external APIs and services
- **Memory Persistence**: Long-term conversation context and investigation history

## Architecture Overview

### 1. State Management

The agent maintains a persistent `AgentState` object that tracks:

```python
class AgentState(TypedDict):
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
```

### 2. Workflow Graph

The agent follows a directed graph of nodes:

```
INPUT_ANALYSIS → [Decision] → CONTEXT_RETRIEVAL → LOG_ANALYSIS → ACTION_GENERATION → STATE_UPDATE
                ↓
            CLARIFICATION → STATE_UPDATE
```

#### Node Descriptions:

- **Input Analysis Node**: Analyzes user input and determines what information is available/missing
- **Context Retrieval Node**: Fetches relevant logs and GCP resource information
- **Log Analysis Node**: Performs AI-powered log analysis using the LLM
- **Clarification Node**: Generates clarifying questions when information is insufficient
- **Action Generation Node**: Suggests next steps and actionable insights
- **State Update Node**: Updates conversation context and persists state

### 3. Conditional Routing

The workflow uses conditional edges to determine the execution path:

```python
workflow.add_conditional_edges(
    "input_analysis",
    self._should_proceed_to_analysis,
    {
        "needs_clarification": "clarification",
        "proceed": "context_retrieval"
    }
)
```

The `_should_proceed_to_analysis` function evaluates the current state and routes accordingly.

## Complete Flow Explanation

### Step 1: Input Analysis

1. **User submits a question** with optional parameters (services, time range, etc.)
2. **Agent analyzes input** to determine what information is provided vs. missing
3. **Decision point**: If sufficient information exists, proceed to analysis; otherwise, ask for clarification

### Step 2: Context Retrieval (if proceeding)

1. **Fetch GCP resource information** to understand available services
2. **Query vector store** for semantically relevant logs
3. **Apply filters** based on user parameters and project context
4. **Format logs** for UI display and analysis

### Step 3: Log Analysis

1. **Build analysis prompt** incorporating:
   - User question
   - Retrieved logs
   - Conversation history
   - Investigation context
2. **Invoke LLM** for AI-powered analysis
3. **Extract insights** and patterns from the logs

### Step 4: Action Generation

1. **Analyze investigation context** to determine focus areas
2. **Generate contextual actions** based on analysis results
3. **Suggest next steps** for continued investigation

### Step 5: State Update

1. **Update conversation context** with new insights
2. **Persist conversation** to session manager
3. **Build context summary** for UI display
4. **Mark workflow as complete**

### Alternative Path: Clarification

If the user's input is insufficient:

1. **Generate specific questions** for missing information
2. **Provide examples** to guide user responses
3. **Update state** to indicate clarification is needed
4. **Wait for user response** before proceeding

## Key Benefits

### 1. **State Persistence**

- Maintains conversation context across multiple interactions
- Tracks investigation progress and insights
- Enables follow-up questions with full context

### 2. **Modular Design**

- Each node has a single responsibility
- Easy to add new nodes or modify existing ones
- Clear separation of concerns

### 3. **Conditional Logic**

- Dynamic workflow based on current state
- Intelligent routing to appropriate nodes
- Handles edge cases gracefully

### 4. **Tool Integration**

- Seamless integration with GCP APIs
- Vector store for semantic search
- Conversation manager for persistence

### 5. **Error Handling**

- Graceful error handling at each node
- State preservation even when errors occur
- Detailed error reporting for debugging

## Usage Examples

### Basic Query

```python
agent = LangGraphAgent()
result = await agent.analyze(
    question="Show me authentication errors from Cloud Run",
    project_id="my-project-123",
    user_id="user@example.com",
    services=["cloud_run_revision"],
    time_range={"start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-02T00:00:00Z"}
)
```

### Follow-up Query (with session)

```python
result = await agent.analyze(
    question="What about the database connection errors?",
    project_id="my-project-123",
    session_id="existing-session-id",  # Continues previous investigation
    user_id="user@example.com"
)
```

## Configuration

### Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash  # Default model
```

### Dependencies

```txt
langgraph
langchain
langchain-google-genai
langchain-core
pydantic
```

## Migration from Old Agent

The new LangGraph agent maintains API compatibility with the previous implementation:

- **Same endpoint**: `/agent/query`
- **Same response format**: Includes all previous fields plus new ones
- **Enhanced features**: Additional fields like `currentStep`, `clarifyingQuestions`
- **Backward compatibility**: Existing frontend code will continue to work

### New Response Fields

```json
{
  "analysis": "AI analysis of logs",
  "sessionId": "session-id",
  "contextSummary": "Current investigation context",
  "actions": [...],
  "needsClarification": false,
  "missingInfo": [],
  "relevantLogs": [...],
  "clarifyingQuestions": [],
  "currentStep": "complete",
  "error": null
}
```

## Future Enhancements

### 1. **Additional Nodes**

- **Correlation Node**: Find patterns across multiple log sources
- **Alerting Node**: Generate alerts based on analysis results
- **Dashboard Node**: Create visual summaries and charts

### 2. **Advanced Routing**

- **Multi-path workflows**: Handle complex investigation scenarios
- **Parallel execution**: Process multiple queries simultaneously
- **Recursive analysis**: Deep-dive into specific areas

### 3. **Tool Expansion**

- **External integrations**: Slack, PagerDuty, etc.
- **Custom tools**: User-defined analysis functions
- **API connectors**: Additional log sources and services

### 4. **Performance Optimization**

- **Caching**: Cache frequently accessed data
- **Async processing**: Parallel execution where possible
- **Resource management**: Optimize memory and API usage

## Troubleshooting

### Common Issues

1. **LangGraph Import Errors**

   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

2. **State Persistence Issues**

   - Verify conversation manager is working
   - Check session TTL settings
   - Ensure proper error handling in state update node

3. **Workflow Execution Errors**
   - Check node function signatures
   - Verify conditional edge logic
   - Ensure all nodes return proper state objects

### Debug Mode

Enable detailed logging by setting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Conclusion

The LangGraph agent implementation provides a robust, scalable foundation for log investigation and analysis. Its state-driven architecture enables complex workflows while maintaining simplicity and extensibility. The modular design makes it easy to add new capabilities and the persistent state ensures continuity across user interactions.

This implementation represents a significant improvement over the previous monolithic approach, providing better separation of concerns, improved error handling, and enhanced user experience through intelligent conversation management.
