# User Stories

## Feature 1: Due dates + overdue filter

### Story 1 — Set a due date on a task
As a task tracker user, I want to set an optional due date when creating or editing a task, so that I know when it needs to be finished.

**Acceptance criteria:**
- `due_date` is optional on both create and update.
- A valid date (e.g. `2026-08-01`) is accepted and returned in the task response.
- A malformed date string (e.g. `"not-a-date"`) is rejected with a 422.
- Omitting `due_date` entirely does not cause an error.

### Story 2 — See at a glance whether a task is overdue
As a task tracker user, I want tasks with a past due date to be clearly marked as overdue, so I can prioritize what needs attention.

**Acceptance criteria:**
- A task is overdue if `due_date` is in the past AND `status` is not `"Done"`.
- A completed (`"Done"`) task is never marked overdue, even if its due date is in the past.
- A task with no `due_date` is never marked overdue.
- `is_overdue` is computed at response time, not stored, so it can't go stale.

### Story 3 — Update a task's due date
As a task tracker user, I want to change a task's due date after creating it, so I can adjust deadlines as plans change.

**Acceptance criteria:**
- `PATCH /tasks/{id}` accepts `due_date` and updates it.
- `is_overdue` recalculates correctly based on the new due date after the update.
- Other fields on the task are unaffected by a due-date-only update.

### Story 4 — Filter the board to only overdue tasks
As a task tracker user, I want to filter my task list to show only overdue tasks, so I can quickly see what's late without scanning the whole board.

**Acceptance criteria:**
- `GET /tasks?overdue=true` returns only tasks where `is_overdue` is true.
- `GET /tasks` with no query param returns all tasks, unfiltered (default behavior unchanged).
- If there are zero overdue tasks, the filtered endpoint returns `200` with an empty list, not an error.

### Story 5 — See and set a due date from the UI
As a task tracker user, I want to set a due date from the task modal in the Kanban board, so I don't have to use the API directly.

**Acceptance criteria:**
- The create/edit modal has a due date input.
- The field is optional — submitting without a due date works.
- Editing an existing task with a due date pre-fills the field with the current value.
- Saving updates the due date and the change persists after a refresh.

---

### AI assumption corrected
While testing manually, an assumption about the task `status` field's format (`"todo"`, lowercase) turned out to be wrong — the project's actual enum values are `"ToDo"`, `"InProgress"`, `"Done"` (capitalized, no separators), defined in `app/models.py`. This was caught immediately via a 422 validation error rather than a silent bug, and the payload was corrected to match the real schema, along with adding the required `priority` field that was initially left out. This reinforced checking the existing model file directly before writing prompts or test payloads, rather than assuming field values.

---

## Feature 2: Tags / labels

### Story 1 — Add tags to a task
As a task tracker user, I want to attach one or more tags to a task, so I can categorize and group related work.

**Acceptance criteria:**
- `tags` is optional on both create and update, defaulting to an empty list if omitted.
- Each tag is trimmed of leading/trailing whitespace before being stored.
- An empty or whitespace-only tag is rejected with a 422.

### Story 2 — Keep tags clean and manageable
As a task tracker user, I want the system to prevent messy or excessive tagging, so tags stay useful for filtering instead of becoming clutter.

**Acceptance criteria:**
- A task may have at most 10 tags; exceeding that returns a 422.
- A single tag may not exceed a fixed max length; exceeding that returns a 422.
- Submitting the same tag twice (case-insensitive) is rejected with a 422 rather than silently modified, so the user is always aware of exactly what they submitted.

### Story 3 — Update a task's tags
As a task tracker user, I want to change a task's tags after creating it, so I can re-categorize work as it evolves.

**Acceptance criteria:**
- `PATCH /tasks/{id}` with `tags` replaces the full existing list — it does not merge or append.
- `PATCH /tasks/{id}` without `tags` in the payload leaves the task's existing tags completely untouched.

### Story 4 — Filter tasks by tag
As a task tracker user, I want to filter the task list by a specific tag, so I can quickly see everything related to a category.

**Acceptance criteria:**
- `GET /tasks?tag=<value>` returns only tasks that have that tag.
- `GET /tasks` with no `tag` param returns all tasks, unfiltered — default behavior is unchanged.
- A tag with no matches returns `200` with an empty list, not an error.

### Story 5 — Manage tags from the UI
As a task tracker user, I want to add, view, and filter by tags directly in the Kanban board, so I don't have to use the API directly.

**Acceptance criteria:**
- The create/edit modal has a tags input that submits fine with zero tags.
- Editing a task with existing tags pre-fills them.
- Tags appear as chips/pills on each card.
- A filter control on the board narrows visible cards by tag.

---

### AI assumption corrected / decision made
When the backend was implemented, the AI's first working version chose to **reject duplicate tags (case-insensitive) with a 422** rather than silently deduplicating them. An earlier draft explored during planning had taken the opposite approach — silently merging duplicates. Neither is objectively "correct"; the decision was made explicitly rather than left to whatever the AI defaulted to, and documented in `mini-adr.md` so the reasoning (make it explicit to the user rather than silently changing their input) is traceable.
