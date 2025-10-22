"""Events router: sync events per company from Eventix API.
"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.eventix_api import EventixClient
from backend.services.supabase_client import SupabaseClient

router = APIRouter()


class EventOut(BaseModel):
    id: str
    company_id: str | None = None
    event_guid: str | None = None
    name: str | None = None


@router.post("/sync", response_model=dict)
async def sync_events(company_guid: str = Query(..., description="Eventix company GUID")) -> dict:
    """Sync events for a company from Eventix API and store in Supabase."""
    eventix = EventixClient()
    supa = SupabaseClient()

    try:
        events = await eventix.fetch_events(company_guid)
        await supa.upsert_events(company_guid, events)
    except Exception as exc:  # noqa: BLE001 broad to surface error
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "ok", "count": len(events)}
