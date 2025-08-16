# Log Analysis Bot

An intelligent log analysis system with RCA (Root Cause Analysis) powered by LangChain.

## Features

- Multi-tenant architecture
- Intelligent log sampling and compression
- Real-time log streaming
- AI-powered root cause analysis
- Scalable to millions of logs

## Quick Start

```bash
docker-compose up -d
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd backend && source venv/bin/activate && uvicorn app.main:app --reload

./scripts/start_filtering_system.sh


```
