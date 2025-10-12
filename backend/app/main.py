from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv
from pathlib import Path

from app.api.main import api_router
from .api.agents.mainAgent import get_main_agent
from .core.config import settings
from agno.os import AgentOS



load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from .core.database import connect_to_mongo, close_mongo_connection
    await connect_to_mongo()
    try:
        yield
    finally:
        await close_mongo_connection()


app = FastAPI(lifespan=lifespan)


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


agent_os = AgentOS(
    agents=[get_main_agent(project_id="default", access_token="default")],
    description="Recce main-agent",
    base_app=app  
)

app = agent_os.get_app()


if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    agent_os.serve(app="custom_fastapi_app:app", reload=True)
