# Task Tracker API

A simple learning-focused REST API for tracking tasks, built with Python and FastAPI. Data persistence uses local JSON file storage to keep the stack minimal and easy to understand (see ADR-001).

## Setup

### 1. Create and activate a virtual environment

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example env file and adjust if needed:

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

## Running the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Testing the health endpoint

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok", "timestamp": "2026-07-08T12:34:56.789012+00:00"}
```

## Running the frontend

The frontend is a static site (no build step needed), but it must be served over HTTP rather than opened directly as a file (`file://`), or the fetch calls to the backend API will be blocked by the browser.

1. Make sure the backend is running first (see "Running the backend" above) — the frontend expects it at `http://localhost:8000`.
2. From the project root, start a simple local server for the frontend:

```bash
   
   python -m http.server 5500
```

3. Open your browser to: