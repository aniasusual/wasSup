# Smart LangGraph Agent - Modular Architecture

This directory contains the refactored Smart LangGraph Agent with a clean, modular architecture that follows best practices for maintainability, readability, and extensibility.

## 🏗️ Architecture Overview

The agent is organized into focused modules with clear separation of concerns:

```
agent/
├── core/                    # Core agent logic and state management
│   ├── agent.py            # Main agent class and orchestration
│   └── state.py            # State definitions and data structures
├── parsers/                # Text parsing and NLP capabilities
│   └── text_parser.py      # Robust natural language processing
├── integrations/           # External service integrations
│   ├── gcp_client.py       # GCP Logging API client
│   └── resource_discovery.py # GCP resource discovery
├── workflows/              # Workflow orchestration
│   └── workflow_builder.py # LangGraph workflow construction
├── nodes/                  # Individual workflow node implementations
│   ├── context_retrieval.py # Log retrieval and filtering
│   └── log_analysis.py     # AI-powered log analysis
└── __init__.py            # Package exports and imports
```

## 🎯 Key Improvements

### 1. **Separation of Concerns**

- **Core Logic**: Agent orchestration and state management
- **Parsing**: Natural language processing and intent recognition
- **Integrations**: External API clients and service discovery
- **Workflows**: Graph construction and node orchestration
- **Nodes**: Individual workflow step implementations

### 2. **Clean Code Practices**

- **Single Responsibility**: Each module has one clear purpose
- **Dependency Injection**: Components are injected rather than tightly coupled
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Logging**: Structured logging throughout all components
- **Type Hints**: Full type annotations for better IDE support

### 3. **Maintainability**

- **Modular Design**: Easy to modify individual components
- **Clear Interfaces**: Well-defined contracts between modules
- **Documentation**: Comprehensive docstrings and comments
- **Testing Ready**: Structure supports unit testing of individual components

### 4. **Extensibility**

- **Plugin Architecture**: Easy to add new nodes or integrations
- **Configuration Driven**: Behavior controlled through configuration
- **Backward Compatibility**: Maintains existing API contracts

## 🔧 Core Components

### Core Agent (`core/agent.py`)

The main orchestrator that:

- Manages the overall workflow execution
- Handles session management and conversation context
- Coordinates between different components
- Provides both streaming and non-streaming interfaces

### State Management (`core/state.py`)

Defines the data structures:

- `AgentState`: TypedDict for workflow state
- `InvestigationStep`: Enum for workflow steps
- `LogEntry`: Structured log representation

### Text Parser (`parsers/text_parser.py`)

Advanced NLP capabilities:

- Fuzzy matching for service and time extraction
- Intent recognition and context understanding
- Natural language time range parsing
- Confidence scoring for extracted information

### GCP Integration (`integrations/`)

- **GCP Logging Client**: Handles API calls with pagination and error handling
- **Resource Discovery**: Discovers available GCP resources for enhanced filtering

### Workflow Builder (`workflows/workflow_builder.py`)

Constructs the LangGraph workflow:

- Node registration and edge definition
- Conditional routing logic
- Workflow compilation

### Workflow Nodes (`nodes/`)

Individual workflow steps:

- **Context Retrieval**: Log fetching with fallback strategies
- **Log Analysis**: AI-powered analysis with intelligent sampling

## 🚀 Usage

### Basic Usage

```python
from app.services.agent import SmartLangGraphAgent

# Initialize the agent
agent = SmartLangGraphAgent()

# Analyze logs
result = await agent.analyze(
    question="What errors occurred in the last hour?",
    project_id="my-gcp-project",
    access_token="oauth2-token"
)
```

### Streaming Usage

```python
# Get real-time progress updates
async for update in agent.analyze_streaming(
    question="Analyze performance issues",
    project_id="my-gcp-project",
    access_token="oauth2-token"
):
    print(update)  # SSE format updates
```

## 🔄 Workflow Flow

1. **Intelligent Analysis**: Parse user input and extract structured information
2. **Decision Routing**: Determine if clarification is needed or proceed with analysis
3. **Context Retrieval**: Fetch logs from GCP with comprehensive pagination
4. **Log Analysis**: AI-powered analysis with intelligent sampling for large datasets
5. **Action Generation**: Generate contextual follow-up actions
6. **Completion**: Update conversation context and format response

## 🛠️ Configuration

The agent can be configured through environment variables:

```bash
# Gemini AI Configuration
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-flash

# GCP Configuration
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

## 🧪 Testing

The modular structure supports comprehensive testing:

```python
# Test individual components
from app.services.agent.parsers.text_parser import RobustTextParser

parser = RobustTextParser()
services = parser.extract_services_robust("cloud run errors")
assert "cloud_run_revision" in [s["type"] for s in services]
```

## 📈 Performance Features

- **Intelligent Sampling**: Handles large datasets efficiently
- **Comprehensive Pagination**: Fetches all available logs
- **Fallback Strategies**: Multiple approaches if primary filters fail
- **Streaming Updates**: Real-time progress feedback
- **Error Recovery**: Graceful handling of API failures

## 🔮 Future Enhancements

The modular architecture enables easy addition of:

- New AI models and analysis engines
- Additional GCP service integrations
- Custom workflow nodes
- Enhanced parsing capabilities
- Performance optimizations

## 📚 Migration Guide

For existing code using the old `langgraph_agent.py`:

```python
# Old way
from app.services.langgraph_agent import SmartLangGraphAgent

# New way (backward compatible)
from app.services.langgraph_agent import SmartLangGraphAgent
# OR
from app.services.agent import SmartLangGraphAgent
```

The API remains the same, but the internal implementation is now much cleaner and more maintainable.
