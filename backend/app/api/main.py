from fastapi import APIRouter
from .routes import auth, logs, project_architecture, agent

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(logs.router)
api_router.include_router(project_architecture.router, prefix="/project-architecture", tags=["project-architecture"])
api_router.include_router(agent.router)
