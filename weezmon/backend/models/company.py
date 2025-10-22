"""Pydantic models for company and related entities."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Company(BaseModel):
    id: str
    name: str | None = None
    company_guid: str
    api_token: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
