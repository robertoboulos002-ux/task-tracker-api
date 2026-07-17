"""
Entry point for the Task Tracker API.

This file creates the FastAPI application instance, loads environment
variables via python-dotenv, and defines the /health endpoint used to
verify the server is running.
"""

from datetime import datetime, timezone
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import storage
from app.business_rules import InvalidStatusTransitionError
from app.models import TaskCreate, TaskResponse, TaskStatus, TaskUpdate

# Load variables from .env (falls back to defaults if .env is missing)
load_dotenv()

# Read config values from environment, with sensible defaults
APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", "8000"))

# Create the FastAPI application instance
app = FastAPI(
    title="Task Tracker API",
    description="A simple task tracker backend using FastAPI and JSON file storage.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    """Response schema for the /health endpoint."""
    status: str
    timestamp: str


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    return storage.add_task(payload)


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(status: Optional[TaskStatus] = None, priority: Optional[str] = None) -> list[TaskResponse]:
    return storage.list_tasks(status=status, priority=priority)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    task = storage.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    try:
        updated_task = storage.update_task(task_id, payload)
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if updated_task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")

    return updated_task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.get("/health", response_model=HealthResponse, status_code=200)
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current server status and an ISO-8601 formatted UTC timestamp.
    Useful for confirming the API is up and reachable.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# Allows running this file directly with `python app/main.py` in addition to uvicorn CLI
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=(APP_ENV == "development"))
