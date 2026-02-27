# New Analytical Trading

This project now uses a **Next.js frontend** with a **FastAPI backend**.

## Project structure

- `app/api.py` — FastAPI API server used by the frontend.
- `core/analysis_models.py` — domain classes (`StockAnalyser`, `Strategiser`).
- `core/analysis_service.py` — orchestration/service helpers used by the API.
- `core/persistence.py` — save/load helpers.
- `core/plotting.py` — chart rendering helpers.
- `frontend/` — Next.js application for dashboard UI.

## Run locally

### 1) Start API server

```bash
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

### 2) Start Next.js frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

The frontend expects the API at `http://localhost:8000` by default.
Override with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```
