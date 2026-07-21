# Mini ADR — Architecture / Decision Record

## Feature 1: Due dates + overdue filter

### Decision
Added an optional `due_date: Optional[date]` field to `TaskCreate`, `TaskUpdate`, and `TaskResponse` in `app/models.py`. Implemented `is_overdue` as a Pydantic `@computed_field` on `TaskResponse`, evaluated at response time as:

```
is_overdue = due_date is not None and status != "Done" and due_date < today
```

Added an optional `overdue: bool | None` query parameter on `GET /tasks` that filters the returned list to only tasks where `is_overdue` is true.

### Alternatives considered / suggested by AI

**Storing `is_overdue` as a persisted field on the task, updated whenever status or due_date changes.**
Rejected. This requires remembering to recompute the flag on every possible mutation path (create, update due_date, update status, and potentially a background job for tasks that silently "become" overdue as time passes). A computed field avoids all of that — it's always correct because it's derived fresh on every read, with zero risk of drift.

**Rejecting past due dates outright at creation time.**
Considered but rejected — a task can legitimately be created with a due date that's already passed (e.g. importing backdated data, or logging a task that was already late when entered). The validation only rejects malformed date strings, not valid-but-past dates.

**Making `due_date` required.**
Rejected as out of scope — the brief specifies it should be optional, and forcing every existing task to have a due date would break backward compatibility with tasks created before this feature existed.

### Rejected as too complex / out of scope
- A scheduled job to recompute/cache overdue status — unnecessary complexity given the computed-field approach handles it for free.
- Due date reminders/notifications — not part of the assigned feature scope (due dates + overdue filter only).
- Timezone-aware due dates/times — the existing schema treats due_date as a plain `date` (no time component), which matches the granularity of the rest of the app. Adding time-of-day would require broader changes to how the app models "today" across timezones, which is out of scope for this feature.

---

## Feature 2: Tags / labels

### Decision
Stored `tags` as a native `list[str]` on the task record (via `TaskCreate`/`TaskUpdate`/`TaskResponse` in `app/models.py`), rather than a normalized comma-separated string. Since the underlying storage is a JSON file (not a relational DB), a JSON-native list is simpler to read/write than parsing and re-joining a delimited string on every access, and it's what the JSON storage layer represents naturally either way.

Validation (trim, reject empty, max 10 tags, max length per tag) lives in a shared validator function used by both `TaskCreate` and `TaskUpdate`, so create and update can't drift out of sync with each other's rules.

`PATCH` semantics: sending `tags` **replaces** the full list (no merge/append); omitting `tags` from the payload **leaves existing tags untouched**. This matches the existing `exclude_unset=True` pattern already used for other optional fields like `due_date`, so no special-case logic was needed for tags specifically.

### Alternatives considered / suggested by AI

**Silently deduplicating tags (case-insensitive) instead of rejecting duplicates.**
An earlier draft took this approach — e.g. `["Urgent", "urgent"]` would silently become `["Urgent"]`. The final implementation instead **rejects duplicate tags with a 422**. Reasoning: silently changing what the user submitted (even for something as small as a duplicate) can be surprising and mask a mistake — e.g. a user who meant to type two *different* tags but fat-fingered the same word twice would get no signal that only one was saved. An explicit 422 keeps the behavior predictable and puts the correction back in the user's hands.

**Storing tags as a comma-separated string field instead of a list.**
Considered because it's slightly more portable for ad-hoc inspection of the raw JSON file. Rejected because it pushes parsing/serialization logic into every place tags are read or written, and it's more error-prone (e.g. a tag itself containing a comma). A native list avoids that class of bug entirely.

### Rejected as too complex / out of scope
- **Tag colors or a color-picker UI** — purely cosmetic, not part of the assigned feature scope.
- **A separate tag-management resource/endpoint** (e.g. `GET/POST /tags` as its own CRUD resource with rename/merge operations) — tags in this feature are just free-text strings attached to a task, not a first-class managed entity. Introducing a separate resource would add relational complexity (what happens to tasks when a tag is renamed or deleted globally?) that's out of scope for a "tags/labels" feature at this size.
- **Tag autocomplete based on previously used tags** — a nice UX addition, but requires aggregating tags across all tasks and exposing that as a new endpoint; deferred as an enhancement rather than core scope.
