"""
JSON file storage layer for tasks, per ADR-001.

Tasks are persisted to a local JSON file (tasks.json). This module exposes
simple functions (add_task, update_task, delete_task, etc.) that main.py
calls directly — no ORM, no database sessions, just read-modify-write on
a JSON file.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.business_rules import InvalidStatusTransitionError, validate_status_transition
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

# Path to the JSON file used as the data store (lives alongside this module's parent folder)
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.json")


def _read_all() -> list[dict]:
    """Read all tasks from the JSON file. Returns an empty list if the file doesn't exist yet."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def _write_all(tasks: list[dict]) -> None:
    """Write the full list of tasks back to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, default=str)


def add_task(payload: TaskCreate) -> TaskResponse:
    """
    Create a new task and persist it to the JSON file.

    status defaults to ToDo if not provided (handled by the TaskCreate model),
    but any valid status may be supplied to start the task elsewhere in the workflow.
    priority is required. assignee is optional.
    """
    tasks = _read_all()
    now = datetime.now(timezone.utc)

    new_task = {
        "id": str(uuid.uuid4()),
        "title": payload.title,
        "description": payload.description,
        "status": payload.status.value,
        "priority": payload.priority.value,
        "assignee": payload.assignee,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    tasks.append(new_task)
    _write_all(tasks)

    return TaskResponse(**new_task)


def get_task(task_id: str) -> Optional[TaskResponse]:
    """Fetch a single task by id. Returns None if not found."""
    tasks = _read_all()
    for task in tasks:
        if task["id"] == task_id:
            return TaskResponse(**task)
    return None


def list_tasks(status: Optional[TaskStatus] = None, priority: Optional[TaskPriority] = None) -> list[TaskResponse]:
    """Return all tasks, optionally filtered by status and/or priority."""
    tasks = _read_all()

    if status is not None:
        tasks = [t for t in tasks if t["status"] == status.value]

    if priority is not None:
        tasks = [t for t in tasks if t["priority"] == priority.value]

    return [TaskResponse(**task) for task in tasks]


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """
    Update an existing task with only the fields provided. Returns None if not found.

    Raises InvalidStatusTransitionError if the requested status change isn't
    allowed by the ToDo -> InProgress -> Done workflow.
    """
    tasks = _read_all()

    for task in tasks:
        if task["id"] == task_id:
            update_data = payload.model_dump(exclude_unset=True)

            if "status" in update_data:
                current_status = TaskStatus(task["status"])
                new_status = TaskStatus(update_data["status"])
                if not validate_status_transition(current_status, new_status):
                    raise InvalidStatusTransitionError(current_status, new_status)
                update_data["status"] = new_status.value

            if "priority" in update_data and update_data["priority"] is not None:
                update_data["priority"] = TaskPriority(update_data["priority"]).value

            task.update(update_data)
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_all(tasks)
            return TaskResponse(**task)

    return None


def delete_task(task_id: str) -> bool:
    """Delete a task by id. Returns True if deleted, False if it didn't exist."""
    tasks = _read_all()
    remaining = [task for task in tasks if task["id"] != task_id]

    if len(remaining) == len(tasks):
        return False  # nothing was removed

    _write_all(remaining)
    return True
