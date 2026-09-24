"""SMS delivery abstraction — console (dev), Twilio or MSG91 (production)."""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def send_sms(phone: str, message: str) -> None:
    provider = settings.SMS_PROVIDER
    try:
        if provider == "twilio" and settings.TWILIO_ACCOUNT_SID:
            async with httpx.AsyncClient(timeout=8) as client:
                await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
                    data={"To": phone, "From": settings.TWILIO_FROM_NUMBER, "Body": message},
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
            return
        if provider == "msg91" and settings.MSG91_AUTH_KEY:
            async with httpx.AsyncClient(timeout=8) as client:
                await client.post(
                    "https://control.msg91.com/api/v5/flow/",
                    headers={"authkey": settings.MSG91_AUTH_KEY, "content-type": "application/json"},
                    json={
                        "template_id": settings.MSG91_TEMPLATE_ID,
                        "recipients": [{"mobiles": phone.lstrip("+"), "message": message}],
                    },
                )
            return
    except Exception as exc:  # pragma: no cover - network
        logger.warning("sms_send_failed", provider=provider, error=str(exc))
    # Console provider / fallback – visible in server logs.
    logger.info("sms_console", to=phone, message=message)
