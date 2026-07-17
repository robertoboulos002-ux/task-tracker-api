# API Testing Cheat Sheet (Windows PowerShell)

Copy-paste these commands to test the Task Tracker API. Replace `PASTE_ID_HERE`
with a real task id (copy it from a POST or GET response).

> **Note:** Always use `curl.exe`, not `curl` — PowerShell aliases `curl` to
> `Invoke-WebRequest`, which uses different flags and will error out.

Make sure the server is running first:
```powershell
uvicorn app.main:app --reload --port 8000
```

---

## Health check

```powershell
curl.exe -i -s http://localhost:8000/health
```

---

## Create a task (expect 201)

```powershell
curl.exe -i -s -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{\"title\": \"Buy groceries\", \"description\": \"Milk, eggs, bread\"}'
```

Copy the `"id"` from the response for the commands below.

---

## List all tasks (expect 200)

```powershell
curl.exe -i -s http://localhost:8000/tasks
```

---

## Get a single task (expect 200, or 404 if not found)

```powershell
curl.exe -i -s http://localhost:8000/tasks/PASTE_ID_HERE
```

---

## Update a task's title (expect 200)

```powershell
curl.exe -i -s -X PATCH http://localhost:8000/tasks/PASTE_ID_HERE -H "Content-Type: application/json" -d '{\"title\": \"New task title\"}'
```

---

## Move status: To Do -> In Progress (expect 200)

```powershell
curl.exe -i -s -X PATCH http://localhost:8000/tasks/PASTE_ID_HERE -H "Content-Type: application/json" -d '{\"status\": \"in_progress\"}'
```

## Move status: In Progress -> Done (expect 200)

```powershell
curl.exe -i -s -X PATCH http://localhost:8000/tasks/PASTE_ID_HERE -H "Content-Type: application/json" -d '{\"status\": \"done\"}'
```

## Reopen: Done -> In Progress (expect 200)

```powershell
curl.exe -i -s -X PATCH http://localhost:8000/tasks/PASTE_ID_HERE -H "Content-Type: application/json" -d '{\"status\": \"in_progress\"}'
```

## Invalid transition example: Done -> To Do (expect 400)

```powershell
curl.exe -i -s -X PATCH http://localhost:8000/tasks/PASTE_ID_HERE -H "Content-Type: application/json" -d '{\"status\": \"to_do\"}'
```

---

## Delete a task (expect 204, no body)

```powershell
curl.exe -i -s -X DELETE http://localhost:8000/tasks/PASTE_ID_HERE
```

---

## Test 404 behavior (task that doesn't exist)

```powershell
curl.exe -i -s http://localhost:8000/tasks/does-not-exist
curl.exe -i -s -X PATCH http://localhost:8000/tasks/does-not-exist -H "Content-Type: application/json" -d '{\"status\": \"done\"}'
curl.exe -i -s -X DELETE http://localhost:8000/tasks/does-not-exist
```

---

## Status code quick reference

| Code | Meaning | When you'll see it |
|---|---|---|
| 200 | OK | Successful GET, successful PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE (no body returned) |
| 400 | Bad Request | Invalid status transition |
| 404 | Not Found | Task id doesn't exist |
| 422 | Unprocessable Content | Request body fails validation (e.g. missing required field, wrong type) |
