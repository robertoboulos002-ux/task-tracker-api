"""
Pydantic models (schemas) for the Task resource.

TaskStatus   - allowed lifecycle states for a task (ToDo -> InProgress -> Done)
TaskPriority - allowed priority levels for a task
TaskCreate   - fields required to create a new task (request body for POST)
TaskUpdate   - fields allowed when updating a task, all optional (request body for PATCH)
TaskResponse - full task shape returned to the client (response body)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Lifecycle states a task can be in. Transitions are validated in app/business_rules.py."""
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    """Priority levels a task can have."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TaskCreate(BaseModel):
    """
    Fields required to create a new task.

    - status is optional and defaults to ToDo, but any valid status may be
      supplied to create a task that starts somewhere else in the workflow.
    - priority is required — there is no default, the client must specify it.
    - assignee is optional.
    """
    title: str = Field(..., min_length=1, max_length=200, description="Short title of the task")
    description: Optional[str] = Field(default=None, max_length=2000, description="Optional longer description")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Starting status. Defaults to ToDo if omitted.")
    priority: TaskPriority = Field(..., description="Priority level. Required — no default.")
    assignee: Optional[str] = Field(default=None, max_length=200, description="Person assigned to the task")


class TaskUpdate(BaseModel):
    """Fields allowed when updating a task. All optional — only provided fields are changed."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TaskStatus] = Field(default=None, description="New status. Must follow a valid transition.")
    priority: Optional[TaskPriority] = Field(default=None)
    assignee: Optional[str] = Field(default=None, max_length=200)


class TaskResponse(BaseModel):
    """Full task representation returned by the API."""
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: datetime
