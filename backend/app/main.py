from fastapi import FastAPI, Query
from app.monitoring.logs import get_logs
# Import routers here (add your routers in api/ and import them)
# from .api import some_router

app = FastAPI()

# Example: app.include_router(some_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the wasSup API!"}

@app.get("/logs")
def read_logs(filter: str = Query(None), limit: int = 50):
    return get_logs(filter, limit)
