"""Eventix API client (v3.0) with request logging and retries.

All requests are logged into Supabase `api_logs` table via SupabaseClient.
"""
from __future__ import annotations

import os
from time import monotonic
from typing import Any, Dict, List

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt

from backend.services.supabase_client import SupabaseClient
from backend.utils.logger import logger


EVENTIX_API_BASE = os.getenv("EVENTIX_API_BASE", "https://api.eventix.io")


class EventixClient:
    """Async client for Eventix API with simple token auth per company."""

    def __init__(self) -> None:
        self._base = EVENTIX_API_BASE.rstrip("/")

    async def _auth_headers(self, company_guid: str | None = None) -> dict:
        # In real usage, tokens should be stored per company in Supabase.
        api_token = os.getenv("EVENTIX_API_TOKEN")
        headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}
        return headers

    @retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(3))
    async def _get(self, endpoint: str, company_id: str | None = None) -> Dict[str, Any]:
        start = monotonic()
        url = f"{self._base}{endpoint}"
        headers = await self._auth_headers()
        status_code = 0
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=headers)
                status_code = resp.status_code
                if resp.status_code == 401:
                    raise httpx.HTTPStatusError("Unauthorized", request=resp.request, response=resp)
                if resp.status_code == 429:
                    raise httpx.HTTPStatusError("Rate limited", request=resp.request, response=resp)
                resp.raise_for_status()
                return resp.json()
        finally:
            elapsed = monotonic() - start
            # Log API call (best-effort; do not block on failure)
            try:
                supa = SupabaseClient()
                supa._client.table("api_logs").insert({
                    "company_id": None,
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "response_time": elapsed,
                }).execute()
            except Exception as log_exc:  # noqa: BLE001
                logger.warning("Failed to log API call", extra={"error": str(log_exc)})

    async def fetch_events(self, company_guid: str) -> List[Dict[str, Any]]:
        # Endpoint path assumed; refer to docs for full reference
        data = await self._get(f"/admin/events/{company_guid}")
        return data.get("data", [])

    async def fetch_sales_statistics(self, company_guid: str) -> Dict[str, Any]:
        return await self._get(f"/admin/sales/statistics/{company_guid}")

    async def fetch_finance(self, company_guid: str) -> Dict[str, Any]:
        return await self._get(f"/admin/finance/{company_guid}")
