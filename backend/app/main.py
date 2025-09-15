from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv
from pathlib import Path

from app.api.main import api_router
from .core.config import settings


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
    start_cleanup_task()
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks when the application stops."""
    from .core.database import close_mongo_connection
    await close_mongo_connection()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)