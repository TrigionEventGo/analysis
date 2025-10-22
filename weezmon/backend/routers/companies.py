"""Companies router: provides CRUD-lite listing and sync endpoints.

Endpoints interact with Supabase to fetch company data.
"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.supabase_client import SupabaseClient

router = APIRouter()


class CompanyOut(BaseModel):
    id: str
    name: str | None = None
    company_guid: str | None = None
    is_active: bool | None = True


@router.get("/", response_model=List[CompanyOut])
async def list_companies() -> List[CompanyOut]:
    """Return list of companies from Supabase."""
    supa = SupabaseClient()
    companies = await supa.list_companies()
    if companies is None:
        raise HTTPException(status_code=500, detail="Failed to fetch companies")
    return [CompanyOut(**c) for c in companies]
