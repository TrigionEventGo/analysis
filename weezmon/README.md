# WeezMon Monorepo

Internal analytics platform for Eventix-based companies and events.

## Run locally

1. Copy `.env.example` to `.env` and fill values.
2. Start Docker services:

```bash
docker compose up --build
```

- FastAPI: http://localhost:8000/health
- Frontend (dev): run `npm install && npm run dev` inside `frontend/` (or deploy to Vercel)
- Metabase: http://localhost:3000

## Tech
- Backend: FastAPI + Celery + Redis
- DB: Supabase (PostgreSQL)
- Frontend: React + Vite + Refine + Tailwind
- Analytics: Metabase
