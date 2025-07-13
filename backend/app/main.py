from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from pathlib import Path
# from fastapi.routing import APIRoute
from app.api.main import api_router
from .core.config import settings

# load_dotenv()
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

print("check: ", settings.API_V1_STR);

# In-memory storage (use Redis or database in production)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)