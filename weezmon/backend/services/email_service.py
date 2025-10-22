"""Email service to send reports via Brevo (Sendinblue) or SMTP.

For simplicity, this module mocks Brevo via sib-api-v3-sdk when configured.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from backend.utils.logger import logger


class EmailService:
    """Wrapper to send report emails via Brevo API."""

    def __init__(self) -> None:
        self._api_key = os.getenv("BREVO_API_KEY")
        self._sender = os.getenv("REPORT_SENDER", "analytics@weezmon.local")
        self._recipient = os.getenv("REPORT_RECIPIENT", "ops@weezmon.local")
        cfg = sib_api_v3_sdk.Configuration()
        if self._api_key:
            cfg.api_key["api-key"] = self._api_key
        self._client = sib_api_v3_sdk.ApiClient(cfg)
        self._email_api = sib_api_v3_sdk.TransactionalEmailsApi(self._client)

    async def send_report(self, company_guid: str, metrics: Dict[str, Any]) -> None:
        """Send a simple email with aggregated metrics."""
        subject = f"WeezMon Report - {company_guid}"
        html_content = f"<h1>Daily Report</h1><pre>{metrics}</pre>"
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": self._recipient}],
            sender={"email": self._sender},
            subject=subject,
            html_content=html_content,
        )
        try:
            self._email_api.send_transac_email(send_smtp_email)
            logger.info("Report email sent", extra={"company_guid": company_guid})
        except ApiException as exc:  # noqa: BLE001
            logger.error("Failed to send email", extra={"error": str(exc)})
