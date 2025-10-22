"""Reports router: trigger Celery report generation and list report logs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.worker import generate_report
from backend.services.supabase_client import SupabaseClient

router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate(company_guid: str = Query(..., description="Eventix company GUID")) -> dict:
    """Trigger report generation task for a company."""
    try:
        res = generate_report.delay(company_guid)
        return {"task_id": res.id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/logs", response_model=list)
async def list_logs() -> list:
    """Return recently generated report logs."""
    supa = SupabaseClient()
    logs = await supa.list_report_logs(limit=100)
    return logs or []
