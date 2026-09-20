"""
Traveo Backend — SMS Integration

Utility to send SMS OTPs using Twilio.
Gracefully handles missing credentials by logging to the console (development mode).
"""
import structlog
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


def send_sms_otp(phone_number: str, otp: str) -> bool:
    """
    Sends an OTP via SMS to the provided phone number.
    Returns True if sent successfully, False otherwise.
    """
    if not getattr(settings, "TWILIO_ACCOUNT_SID", None) or not getattr(settings, "TWILIO_AUTH_TOKEN", None):
        logger.warning(
            "twilio_credentials_missing",
            message="Twilio credentials not found. Simulating OTP SMS.",
            phone=phone_number,
            otp=otp
        )
        return True

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Determine the From number to use
        from_number = getattr(settings, "TWILIO_FROM_NUMBER", None)
        
        if not from_number:
            logger.error("twilio_from_number_missing")
            return False

        message = client.messages.create(
            body=f"Your Traveo verification code is {otp}. It expires in 5 minutes.",
            from_=from_number,
            to=phone_number,
        )
        logger.info("twilio_sms_sent", message_sid=message.sid, phone=phone_number)
        return True
    except TwilioRestException as e:
        logger.error("twilio_sms_failed", error=str(e), phone=phone_number)
        return False
    except Exception as e:
        logger.error("sms_send_failed", error=str(e), phone=phone_number)
        return False
