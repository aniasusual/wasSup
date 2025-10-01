# Log Analysis Bot

An intelligent log analysis system with RCA (Root Cause Analysis) powered by LangChain and LangGraph.

## Features

- Multi-tenant architecture
- Intelligent log sampling and compression
- Real-time log streaming
- Advanced log analysis and filtering
- Scalable to millions of logs

## Architecture

### Log Analysis System

The system provides comprehensive log analysis capabilities:

- **Real-time log streaming** from Google Cloud Platform
- **Advanced filtering and querying** with GCP Logging API
- **Multi-project support** with project architecture management
- **Scalable log processing** for large-scale deployments
- **Secure authentication** with Google OAuth2

## Quick Start

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/
│   ├── api/                    # API routes and endpoints
│   │   ├── routes/            # Route handlers (auth, logs, project_architecture)
│   │   ├── helpers/           # Authentication helpers
│   │   └── data/              # API endpoint configurations
│   ├── core/                  # Core configuration and database
│   ├── models/                # Data models
│   │   └── user.py            # User models
│   └── services/              # Business logic services
│       ├── user_service.py    # User management
│       ├── project_architecture_service.py  # Architecture management
│       ├── conversation_manager.py          # Conversation state management
│       └── session_cleanup.py               # Session cleanup tasks
├── requirements.txt           # Python dependencies
```

## Features

- **Advanced Log Analysis**: Comprehensive log filtering and analysis capabilities
- **GCP Integration**: Direct integration with Google Cloud Logging and Resource Manager
- **Authentication**: OAuth2 with Google for secure access
- **Project Architecture**: Support for storing and analyzing project architecture
- **Conversation Management**: Persistent conversation state with cleanup
- **Streaming Responses**: Real-time streaming for long-running operations

## API Endpoints

### Log Analysis Endpoints

- `POST /logs/query` - Query logs with advanced filtering
- `GET /logs/projects` - Get available GCP projects
- `POST /logs/gcp-resource-options` - Get GCP resource options

### Response Format

The API provides structured responses for log analysis:

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
