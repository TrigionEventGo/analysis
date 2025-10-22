"""Pydantic model for report log."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ReportLog(BaseModel):
    id: str
    company_guid: str
    total_sales: float
    total_refunds: float
    created_at: datetime | None = None
