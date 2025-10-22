"""Celery tasks for WeezMon.

Contains tasks to generate analytics reports and fetch finance data from
Eventix. Tasks should be idempotent and log progress. External I/O is done
via service modules.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict
from celery import shared_task
from tenacity import retry, wait_exponential, stop_after_attempt

from backend.utils.logger import logger
from backend.services.eventix_api import EventixClient
from backend.services.supabase_client import SupabaseClient
from backend.services.email_service import EmailService


@shared_task(name="generate_report")
@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(3))
def generate_report(company_guid: str) -> dict:
    """Generate daily report for a company and email the results.

    This function runs in Celery worker context. It bridges to async
    services via asyncio.
    """
    logger.info("Starting report generation", extra={"company_guid": company_guid})

    async def _async_impl() -> Dict[str, Any]:
        eventix = EventixClient()
        supa = SupabaseClient()
        email = EmailService()

        stats = await eventix.fetch_sales_statistics(company_guid)
        # Aggregate metrics (placeholder - depends on exact API shape)
        total_sales = sum(item.get("revenue", 0) for item in stats.get("data", []))
        total_refunds = sum(item.get("refunds", 0) for item in stats.get("data", []))

        report_record = {
            "company_guid": company_guid,
            "total_sales": total_sales,
            "total_refunds": total_refunds,
        }
        await supa.insert_report_log(report_record)

        await email.send_report(company_guid=company_guid, metrics=report_record)
        return report_record

    return asyncio.run(_async_impl())


@shared_task(name="fetch_finance_data")
@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(3))
def fetch_finance_data(company_guid: str) -> dict:
    """Fetch finance data like fees, refunds, invoices for a company."""
    logger.info("Fetching finance data", extra={"company_guid": company_guid})

    async def _async_impl() -> Dict[str, Any]:
        eventix = EventixClient()
        supa = SupabaseClient()

        finance = await eventix.fetch_finance(company_guid)
        await supa.store_finance_data(company_guid, finance)
        return {"status": "ok"}

    return asyncio.run(_async_impl())
