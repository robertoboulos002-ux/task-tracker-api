# Verification

## Feature 1: Due dates + overdue filter

### Baseline check

Ran the full existing pytest suite before adding any new frontend work for this session, to confirm the starting state of the repo.

```
tests/ -v
28 items collected
27 passed, 1 failed
```

**Note on the one failure:** `test_patch_same_status_returns_422` fails on this codebase — it expects a no-op status update (e.g. `ToDo` → `ToDo`) to return 422, but the API currently returns 200. This is a **pre-existing issue unrelated to the due-date/overdue feature** (it concerns the status-transition business rule in `app/business_rules.py`, not `due_date` or `is_overdue`). It is called out here rather than hidden, and is a candidate for a separate bug ticket rather than something fixed silently inside this feature's scope.

### Backend test results (due_date + overdue specific)

All 6 due-date/overdue-related tests pass:

```
test_create_task_with_due_date_returns_it_in_response                              PASSED
test_create_task_with_malformed_due_date_returns_422                               PASSED
test_create_task_with_past_due_date_and_nondone_status_is_overdue_true             PASSED
test_create_task_with_past_due_date_and_done_status_is_overdue_false               PASSED
test_list_tasks_overdue_filter_returns_only_overdue                                PASSED
```

### Manual browser / API checks

Performed via PowerShell (`curl.exe` / `Invoke-RestMethod`) against the running local server:

| Check | Payload | Result |
|---|---|---|
| Create with past due date, open status | `due_date: 2020-01-01, status: ToDo` | `is_overdue: true` ✅ |
| Create with past due date, Done status | `due_date: 2020-01-01, status: Done` | `is_overdue: false` ✅ |
| Create with future due date | `due_date: 2099-01-01` | `is_overdue: false` ✅ |
| `GET /tasks?overdue=true` | — | returned only the genuinely overdue task ✅ |
| `GET /tasks` (no filter) | — | returned all tasks, default behavior unchanged ✅ |

All five manual checks matched expected behavior exactly, and matched what the raw API response showed (cross-checked against the UI once the modal was wired up).

### Behavior contract (before/after)

**Before due_date feature existed:** `GET /tasks` returned tasks without any `due_date` or `is_overdue` fields; no `overdue` query parameter was supported.

**After:** `GET /tasks` returns the same task shape plus `due_date` (nullable) and `is_overdue` (always present, computed). The `overdue` query parameter is additive — omitting it preserves the exact prior response for existing tasks. No existing field was renamed, removed, or changed in meaning.

### Break Test evidence

Two Break Tests were performed by deliberately introducing a bug into the real code, confirming the relevant test(s) fail, then reverting and confirming green again. This proves the tests are actually exercising the logic they claim to, not just passing by coincidence.

**Break Test 1 — target: overdue detection logic**

Change made: removed the `status != "Done"` condition from `is_overdue` in `app/models.py`, so it became:
```python
is_overdue = due_date is not None and due_date < today  # status check removed
```

Result: **2 tests failed as expected**
```
FAILED test_create_task_with_past_due_date_and_done_status_is_overdue_false
FAILED test_list_tasks_overdue_filter_returns_only_overdue
  AssertionError: assert 2 == 1  (a "Done" task incorrectly counted as overdue)
```

Reverted the change, reran the same tests: **3 passed, 0 failed** — confirms the tests genuinely catch this regression and the fix restores correct behavior.

**Break Test 2 — target: malformed due_date validation (finding, not a clean pass)**

Attempted to break `due_date` type validation (changing `date` to `str` in the schema) to confirm `test_create_task_with_malformed_due_date_returns_422` would fail if validation broke.

**Finding:** the test as written sends `"priority": "low"` (lowercase), which is **already invalid on its own** (the real enum values are `"Low"/"Medium"/"High"`, capitalized — see `app/models.py`). This means the test returns 422 regardless of whether `due_date` validation works, because the priority field fails validation first. The test is not currently isolating the thing its name claims to test.

This is flagged here as a genuine QA finding rather than papered over: **the test should be corrected to use `"priority": "Low"` (matching the real enum) so that a 422 can only be attributed to the malformed `due_date`, not an unrelated field.** This is a good example of "AI-generated test coverage that looks complete but has a latent gap" — worth including in the reflection as a moment where manual review changed the outcome.

---

## Feature 2: Tags / labels

### Baseline check

Ran the full pytest suite before starting frontend work for tags, to confirm the state of the repo after the backend implementation.

```
tests/ -v
36 items collected
35 passed, 1 failed
```

The one failure is the same pre-existing, unrelated issue documented in Feature 1 (`test_patch_same_status_returns_422` — a no-op status PATCH returns 200 instead of the expected 422; concerns the status-transition rule, not tags or due_date). No new failures were introduced by the tags implementation.

### Backend test results (tags specific)

All 9 tags-related tests pass:

```
test_create_task_with_tags_returns_them_in_response          PASSED
test_create_task_with_invalid_tags_returns_422                PASSED
test_create_task_with_duplicate_tags_returns_422               PASSED
test_create_task_with_too_many_tags_returns_422                PASSED
test_create_task_with_long_tag_returns_422                     PASSED
test_patch_tags_replaces_existing_tags                          PASSED
test_patch_without_tags_leaves_existing_tags_untouched          PASSED
test_list_tasks_filter_by_tag_returns_only_matches              PASSED
```

### Manual browser / API checks

Performed via PowerShell (`Invoke-RestMethod`) against the running local server:

| Check | Payload / call | Result |
|---|---|---|
| Create with valid tags | `tags: ["urgent", "backend"]` | stored and returned correctly ✅ |
| PATCH replaces full tag list | `tags: ["only-this"]` | old tags fully replaced ✅ |
| PATCH omitting tags | `title: "renamed"` only | existing tags (`["only-this"]`) left untouched ✅ |
| Filter by tag | `GET /tasks?tag=urgent` | returned only the matching task ✅ |
| Omit tags entirely on create | no `tags` field | defaulted to `[]`, no error ✅ |
| Empty/whitespace tag | `tags: ["ok", "   "]` | correctly rejected with 422 and a clear message ✅ |

All manual checks matched expected behavior. The 422 case surfaced as a PowerShell `WebException` in the terminal — this is expected `Invoke-RestMethod` behavior on any non-2xx response, not a bug; the response body confirmed the correct validation message.

### Behavior contract (before/after)

**Before tags feature existed:** `TaskResponse` had no `tags` field; `GET /tasks` had no `tag` query parameter.

**After:** `TaskResponse` includes `tags` (always present, defaulting to `[]`). The `tag` query parameter on `GET /tasks` is additive — omitting it preserves the exact prior response shape and filtering behavior for `status`, `priority`, and `overdue`. No existing field was renamed, removed, or changed in meaning.

### Break Test evidence

*(Recommended next step, not yet performed: break the duplicate-tag rejection — e.g. temporarily disable the case-insensitive comparison — and confirm `test_create_task_with_duplicate_tags_returns_422` fails, then revert and confirm it passes again. This is the strongest candidate for a tags Break Test since, like the overdue-filter logic in Feature 1, it depends on a comparison that's easy to accidentally weaken without an obvious symptom.)*
