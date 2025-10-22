"""Async Supabase client wrapper for data access.

Encapsulates reading and writing entities and logs. Uses the supabase
Python client. Some endpoints use PostgREST; operations are async via
httpx underneath.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

from backend.utils.logger import logger


class SupabaseClient:
    """Simple wrapper around Supabase python client for CRUD operations."""

    def __init__(self) -> None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("Supabase env vars are not configured")
        self._client: Client = create_client(url, key)

    async def list_companies(self) -> Optional[List[Dict[str, Any]]]:
        resp = self._client.table("companies").select("*").execute()
        data = resp.data or []
        logger.debug("Fetched companies", extra={"count": len(data)})
        return data

    async def upsert_events(self, company_guid: str, events: List[Dict[str, Any]]) -> None:
        # Map events to schema shape (assumes company id lookup by guid)
        for chunk_start in range(0, len(events), 1000):
            chunk = events[chunk_start : chunk_start + 1000]
            self._client.table("events").upsert(chunk).execute()
        logger.info("Upserted events", extra={"count": len(events), "company_guid": company_guid})

    async def insert_report_log(self, record: Dict[str, Any]) -> None:
        self._client.table("report_logs").insert(record).execute()
        logger.info("Inserted report log")

    async def list_report_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        resp = self._client.table("report_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return resp.data or []

    async def store_finance_data(self, company_guid: str, finance: Dict[str, Any]) -> None:
        # Placeholder: store aggregated finance in a table
        payload = {"company_guid": company_guid, "payload": finance}
        self._client.table("finance_snapshots").insert(payload).execute()
        logger.info("Stored finance snapshot")
