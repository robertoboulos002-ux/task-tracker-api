"""
Business rules for task status transitions.

Enforces this workflow:
    ToDo -> InProgress -> Done
    Done -> InProgress   (reopening a completed task)

No skipping stages (ToDo -> Done directly is not allowed), no moving
directly from Done back to ToDo, and no no-op transitions (setting a
status to its own current value is rejected).
"""

from app.models import TaskStatus

# Maps each status to the set of statuses it is allowed to move to next.
_ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.DONE},
    TaskStatus.DONE: {TaskStatus.IN_PROGRESS},  # allow reopening a completed task
}


class InvalidStatusTransitionError(Exception):
    """Raised when a task's status is changed to a value that isn't a valid next step."""
    def __init__(self, current_status: TaskStatus, new_status: TaskStatus):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Cannot transition task from '{current_status.value}' to '{new_status.value}'. "
            f"Allowed order is: ToDo -> InProgress -> Done (Done may reopen to InProgress)."
        )


def validate_status_transition(current_status: TaskStatus, new_status: TaskStatus) -> bool:
    """
    Return True if moving from current_status to new_status is a valid transition.

    Setting a status to its own current value (no-op) is treated as invalid —
    the caller must choose a genuinely different, allowed next status.
    """
    return new_status in _ALLOWED_TRANSITIONS.get(current_status, set())