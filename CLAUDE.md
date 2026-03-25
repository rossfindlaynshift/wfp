# CLAUDE.md

## Project Overview

Workforce Planning (WFP) application — replaces an Excel-based workforce planning spreadsheet. Python/FastAPI backend + React/TypeScript frontend, running locally on macOS.

## Tech Stack

- **Backend:** Python 3.9, FastAPI, SQLAlchemy, SQLite (PostgreSQL-ready schema)
- **Frontend:** React, Vite, TypeScript, TailwindCSS v4, AG Grid Community
- **Data:** SQLite database at `data/wfp.db`, seeded from existing spreadsheet

## Running Locally

```bash
# Backend (terminal 1)
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && npm run dev
```

Frontend runs at http://localhost:5173 with Vite proxy to backend at :8000.

## Key Commands

- **Seed reference data:** `cd backend && source venv/bin/activate && python seed_from_spreadsheet.py`
- **TypeScript check:** `cd frontend && npx tsc --noEmit`
- **Frontend build:** `cd frontend && npx vite build`

## Project Structure

- `plan.md` — full implementation plan with phases, data model, and cost engine spec
- `backend/app/models/` — SQLAlchemy models (reference, census, forecast)
- `backend/app/routers/` — API route handlers
- `backend/app/schemas/` — Pydantic request/response models
- `backend/app/services/` — Business logic (cost engine, HiBob client, etc.)
- `frontend/src/components/` — React components organised by feature area
- `frontend/src/services/api.ts` — API client
- `frontend/src/types/` — TypeScript interfaces

## Workflow Rules

- **After completing each phase, update README.md** with current setup instructions, features available, and any new dependencies or configuration needed.
- Refer to `plan.md` for the implementation plan, data model, cost calculation logic, and phase breakdown.
- The existing spreadsheet at the project root (`nShift Census Example anonymised.xlsx`) is the source of truth for reference data structure and seed values.
