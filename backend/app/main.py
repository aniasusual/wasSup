from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv
from pathlib import Path

from app.api.main import api_router
from .core.config import settings
from .models.agent import WorkflowConfig
from .services.agent.core import GCPLogInvestigationAgent


load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage (use Redis or database in production)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Startup tasks when the application starts."""
    from .services.session_cleanup import start_cleanup_task
    from .core.database import connect_to_mongo
    app.state.agent = GCPLogInvestigationAgent(
        WorkflowConfig(
            max_api_calls_per_session=50,
            max_investigation_time_minutes=30,
            confidence_threshold=0.7,
            enable_streaming=True,
            enable_learning=True,
            debug_mode=True,
        )
    )
    start_cleanup_task()
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks when the application stops."""
    from .core.database import close_mongo_connection
    if getattr(app.state, "agent", None) is not None:
        app.state.agent = None
    await close_mongo_connection()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
