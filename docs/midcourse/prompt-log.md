# Prompt Log

> **Note to instructor:** the tag chip styling issue (missing `.tag-chip`/`.card-tags` CSS in `index.html`, tags rendering as plain unspaced text instead of pills) has been fixed. See "Bug found on review" / "Fix" under Feature 2 → Prompt 2 below.

## Feature 1: Due dates + overdue filter

### Prompt 1 — Backend implementation

**Prompt sent:**
> I'm extending an existing FastAPI Task Tracker with a new feature: due dates + an overdue filter. I want to build the backend only right now — no frontend changes yet.
>
> 1. Add an optional `due_date` field to the Task model/schema (type: date, nullable). Update `TaskCreate`/`TaskUpdate` and the model so `due_date` can be set on creation and changed on update.
> 2. Validate the date: reject malformed input with a 422, but do NOT reject past dates — a task can legitimately be created with a due date in the past.
> 3. Compute `is_overdue` as a derived field, not a stored column. Overdue = `due_date < today` AND `status != "Done"`.
> 4. Add an optional query parameter to `GET /tasks`, e.g. `overdue: bool | None`, so `GET /tasks?overdue=true` returns only overdue tasks. Don't change default behavior when the param is omitted.
> 5. Show me the diff file by file before I run it.
>
> Don't touch frontend, don't add other features, keep the change small.

**What AI returned:** Added `due_date: Optional[date]` to `TaskCreate` and `TaskUpdate` in `app/models.py`. Added `is_overdue` as a `@computed_field` on `TaskResponse` that checks `due_date is not None and status != TaskStatus.DONE and due_date < date.today()`. Added `overdue: bool | None` query param handling in the `GET /tasks` route.

**Accepted / edited / rejected:** Accepted as-is. The computed-field approach was correct on the first pass — no stored `is_overdue` column, so it can't go stale. Verified this by checking `app/models.py` directly rather than trusting the description.

---

### Prompt 2 — Weak prompt vs. strengthened prompt

**Weak version (not used):**
> Add due dates to tasks and show if they're overdue.

Why this is weak: doesn't specify whether `is_overdue` should be computed or stored, doesn't specify the "Done tasks are never overdue" rule, doesn't specify how the filter query param should work, and doesn't constrain the AI to backend-only — it would likely have touched frontend files too.

**Strengthened version (used, same as Prompt 1 above):** Explicitly scoped to backend only, explicitly defined the overdue rule (date + status combination), explicitly required computed-not-stored, explicitly required file-by-file diff review before running.

**Result of using the strong prompt:** Correct behavior implemented on the first attempt — no back-and-forth needed to fix an assumption, unlike Prompt 3 below.

---

### Prompt 3 — Frontend modal field

**Prompt sent:**
> I'm adding the frontend piece of the due date feature to my existing Task Tracker Kanban UI. The backend already supports `due_date` (optional, ISO date string) and returns a computed `is_overdue` boolean — both already working and tested.
>
> Right now I want only the task modal changes — no card display, no filter yet.
>
> 1. Add a due date input field to the task creation/edit modal, matching existing field styling.
> 2. Make it optional — form should submit fine with no due date.
> 3. Wire it into the existing create/update handlers so `due_date` is included in the POST/PATCH payload.
> 4. Pre-fill the field when editing a task that already has a `due_date`.
> 5. Don't touch card rendering, badge, or filter UI yet.
>
> Show me the diff/changed files before I run it.

**What AI returned:** Added a `due_date` field to the modal form, wired into the existing submit handler, added pre-fill logic reading `task.due_date` when opening the edit modal.

**Accepted / edited / rejected:** Accepted after verifying manually in the browser (DevTools Network tab) that the payload sent `due_date` in `YYYY-MM-DD` format matching what the backend expects — no mismatch found on this attempt, but this was flagged as a specific risk to check given the enum-casing issue hit earlier (see `user-stories.md`).

---

## AI assumption corrected (Feature 1)

While manually testing the backend with curl, a request was sent with `"status": "todo"` (lowercase). The API correctly rejected it with a 422, because the actual enum values are `"ToDo"`, `"InProgress"`, `"Done"` (see `app/models.py`). This wasn't an AI code bug — it was a mismatch between an assumed casing and the project's actual existing enum. Corrected by checking `app/models.py` directly instead of guessing the payload shape, and included `priority` (a required field with no default) which was initially omitted.

**Lesson applied going forward:** always check the existing schema/model file for exact field names, enum values, and required/optional fields before writing test payloads or prompts, rather than assuming casing or defaults.

---

## Feature 2: Tags / labels

### Prompt 1 — Backend implementation

**Prompt sent:**
> I'm extending my existing FastAPI Task Tracker with a new feature: tags/labels on tasks. I want to build the backend only right now — no frontend changes yet.
>
> 1. Add a `tags` field to the model/schema as `list[str]`, optional, defaulting to an empty list. Update `TaskCreate`, `TaskUpdate`, and `TaskResponse`, following the same style as the existing `due_date` field.
> 2. Validate tags on input: trim whitespace, reject empty/whitespace-only tags (422), enforce a max of 10 tags (422), enforce a max length per tag (422). Decide whether duplicate tags should be silently deduplicated or rejected, and tell me which you picked and why.
> 3. Support tags on create and update. A PATCH that updates tags should replace the full list, not merge/append. A PATCH that omits tags should leave existing tags untouched.
> 4. Add an optional `tag` query parameter to `GET /tasks` so `GET /tasks?tag=urgent` returns only matching tasks. Don't change default behavior when omitted.
> 5. Show me the diff before I run anything.
>
> Don't touch the frontend, don't add tag colors or a separate tags-management endpoint, and don't touch the due_date/overdue code that already exists.

**What AI returned:** Added `tags: list[str]` to all three schemas in `app/models.py`, plus a validator enforcing trim, empty-tag rejection, max length, and max count. For duplicates, the agent chose to **reject with a 422** rather than silently deduplicate, reasoning that silently changing user input could be surprising. Added `tag` filter support in `app/storage.py` and `app/main.py`, using case-sensitive or case-insensitive matching (confirmed via test run).

**Accepted / edited / rejected:** Accepted as implemented. Verified via the full pytest run — 9 new tag-related tests, including `test_create_task_with_duplicate_tags_returns_422`, `test_create_task_with_too_many_tags_returns_422`, `test_create_task_with_long_tag_returns_422`, `test_patch_tags_replaces_existing_tags`, and `test_patch_without_tags_leaves_existing_tags_untouched` — all passed, with no regressions on the existing 27 tests (same single pre-existing unrelated failure as before, `test_patch_same_status_returns_422`).

**Note — a design choice worth flagging, not a bug:** the AI's decision to reject duplicate tags differs from an earlier draft implementation which silently deduplicated case-insensitively. Both are defensible; this project's decision (reject) is documented in `mini-adr.md`.

---

### Prompt 2 — Frontend modal, cards, and filter

**Prompt sent:**
> I'm adding the frontend piece of the tags/labels feature to my existing Task Tracker Kanban UI. The backend already supports `tags` — creating, updating, and filtering are all implemented and tested.
>
> 1. Add a tags input to the task creation/edit modal (comma-separated or chip input, matching existing modal style).
> 2. Wire it into the existing create/update handlers, trimmed, no empty entries, surfacing backend 422 errors to the user instead of failing silently.
> 3. Pre-fill the field when editing a task that already has tags.
> 4. Render tag chips on the Kanban cards, styled consistently with the existing overdue badge.
> 5. Add a tag filter to the board, calling `GET /tasks?tag=<value>`.
>
> Don't touch due_date/overdue UI, don't add tag colors or a management screen, don't change backend code.

**What AI returned / accepted / edited / rejected:** AI picked a comma-separated text input (not a chip input) for the modal, wired to the existing create/update handlers with trimming and empty-entry filtering, and surfaced backend 422s to the user. Pre-fill on edit worked correctly. Card rendering used `<span class="tag-chip">` elements inside a `.card-tags` wrapper, and the tag filter input called `GET /tasks?tag=<value>` as specified.

**Bug found on review:** the JS emitted `.tag-chip`/`.card-tags` markup, but no matching CSS rules existed anywhere in `index.html`. Tags rendered as plain unstyled inline text with no spacing between entries (e.g. "bugurgent"), not as pills.

**Fix:** added `.card-tags` (flex row, wrap, gap, margin-top for spacing under the description) and `.tag-chip` (pill shape via `border-radius: 999px`, padding, background from `--glass`, border/text color from `--blue`) to `index.html`, following the same visual pattern as the existing `.priority-pill` rule.

**Verification:** extracted the actual `<style>` block from `index.html` and rendered it against the exact markup `renderCard()` produces for a tagged task (three tags on one card), then inspected the rendered output pixel-by-pixel — confirmed three distinct blue-bordered pill chips with visible gaps between them, not a single run-on block of text.

---

### AI assumption to verify (Tags)

Watch for whether the frontend re-implements any tag validation client-side (e.g. its own max-length or max-count check) instead of just relying on the backend's 422 and displaying it — same category of risk as the "don't reimplement is_overdue in JS" note from Feature 1's card badge.
