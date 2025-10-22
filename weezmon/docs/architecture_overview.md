# WeezMon Architecture Overview

WeezMon is an internal analytics platform to monitor Eventix-based companies and events.

## Components
- Backend (FastAPI + Celery + Redis)
- Database (Supabase / PostgreSQL)
- Frontend (React + Refine + Tailwind)
- Analytics (Metabase)

## Data Flow
1. Celery (optionally with Beat) schedules daily fetches from Eventix.
2. FastAPI exposes endpoints to trigger syncs and fetch metrics.
3. Supabase stores raw and aggregated data; Metabase renders dashboards.
4. Frontend consumes FastAPI endpoints and visualizes metrics.

## Environment
- Secrets via environment variables (.env)
- Docker Compose for local development
