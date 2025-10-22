"""Finance router: fetch fees and store in Supabase."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.worker import fetch_finance_data

router = APIRouter()


@router.post("/fetch", response_model=dict)
async def fetch_finance(company_guid: str = Query(..., description="Eventix company GUID")) -> dict:
    """Trigger asynchronous finance data fetch task."""
    try:
        res = fetch_finance_data.delay(company_guid)
        return {"task_id": res.id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
