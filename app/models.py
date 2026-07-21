"""
Pydantic models (schemas) for the Task resource.

TaskStatus   - allowed lifecycle states for a task (ToDo -> InProgress -> Done)
TaskPriority - allowed priority levels for a task
TaskCreate   - fields required to create a new task (request body for POST)
TaskUpdate   - fields allowed when updating a task, all optional (request body for PATCH)
TaskResponse - full task shape returned to the client (response body)
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field, model_validator


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


MAX_TAGS = 10
MAX_TAG_LENGTH = 50


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized_tags: list[str] = []
    seen_lower: set[str] = set()

    for tag in tags:
        trimmed = tag.strip()
        if not trimmed:
            raise ValueError("Tags must not be empty or whitespace-only.")
        if len(trimmed) > MAX_TAG_LENGTH:
            raise ValueError(
                f"Each tag must be at most {MAX_TAG_LENGTH} characters long."
            )
        lower_tag = trimmed.lower()
        if lower_tag in seen_lower:
            raise ValueError(
                "Duplicate tags are not allowed. Tags are compared case-insensitively."
            )
        seen_lower.add(lower_tag)
        normalized_tags.append(trimmed)

    if len(normalized_tags) > MAX_TAGS:
        raise ValueError(f"No more than {MAX_TAGS} tags are allowed.")

    return normalized_tags


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
    due_date: Optional[date] = Field(default=None, description="Optional due date for the task")
    tags: list[str] = Field(default_factory=list, description="Optional tags for the task.")

    @model_validator(mode="before")
    def _normalize_tags(cls, values):
        if "tags" not in values:
            return values

        tags = values["tags"]
        if tags is None:
            values["tags"] = []
            return values

        values["tags"] = _normalize_tags(tags)
        return values


class TaskUpdate(BaseModel):
    """Fields allowed when updating a task. All optional — only provided fields are changed."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TaskStatus] = Field(default=None, description="New status. Must follow a valid transition.")
    priority: Optional[TaskPriority] = Field(default=None)
    assignee: Optional[str] = Field(default=None, max_length=200)
    due_date: Optional[date] = Field(default=None, description="Optional due date for the task")
    tags: Optional[list[str]] = Field(default=None, description="Optional tags for the task. Replaces existing tags when provided.")

    @model_validator(mode="before")
    def _normalize_tags(cls, values):
        if "tags" not in values or values["tags"] is None:
            return values

        values["tags"] = _normalize_tags(values["tags"])
        return values


class TaskResponse(BaseModel):
    """Full task representation returned by the API."""
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    tags: list[str] = Field(default_factory=list, description="Tags attached to the task.")
    created_at: datetime
    updated_at: datetime

    @computed_field
    def is_overdue(self) -> bool:
        return (
            self.due_date is not None
            and self.status != TaskStatus.DONE
            and self.due_date < date.today()
        )
