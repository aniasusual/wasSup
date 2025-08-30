# Log Analysis Bot

An intelligent log analysis system with RCA (Root Cause Analysis) powered by LangChain and LangGraph.

## Features

- Multi-tenant architecture
- Intelligent log sampling and compression
- Real-time log streaming
- AI-powered root cause analysis with LangGraph agent
- Scalable to millions of logs
- State-driven conversation management
- Intelligent workflow routing

## Architecture

### LangGraph Agent System

The system now uses **LangGraph** for building intelligent, state-driven agents that can:

- **Maintain conversation state** across multiple interactions
- **Route workflows intelligently** based on user input and context
- **Handle complex multi-step investigations** with conditional logic
- **Provide persistent memory** for long-running conversations
- **Generate contextual actions** and follow-up suggestions

#### Key Components

- **State Management**: Persistent `AgentState` objects track investigation progress
- **Workflow Nodes**: Specialized nodes for input analysis, context retrieval, log analysis, and more
- **Conditional Routing**: Dynamic decision-making based on current state
- **Tool Integration**: Seamless integration with GCP APIs, vector stores, and conversation management

For detailed information about the LangGraph implementation, see [docs/LANGGRAPH_AGENT_IMPLEMENTATION.md](docs/LANGGRAPH_AGENT_IMPLEMENTATION.md).

## Quick Start

```bash
docker-compose up -d
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd backend && source venv/bin/activate && uvicorn app.main:app --reload

./scripts/start_filtering_system.sh
```

## Testing the LangGraph Agent

To test the new agent implementation:

```bash
cd backend
python test_langgraph_agent.py
```

This will run comprehensive tests demonstrating the agent's capabilities including:

- Complete vs. incomplete information handling
- Session management and conversation history
- Workflow execution and state management
- Error handling and recovery

## API Endpoints

### Agent Endpoints

- `POST /agent/query` - Submit a question for analysis
- `GET /agent/sessions` - Get user's active sessions
- `GET /agent/sessions/{session_id}/history` - Get conversation history
- `DELETE /agent/sessions/{session_id}` - Delete a session
- `GET /agent/resources/{project_id}` - Discover GCP resources
- `GET /agent/resources/{project_id}/summary` - Get resource summary

### Enhanced Response Format

The new agent provides enhanced responses with additional fields:

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
