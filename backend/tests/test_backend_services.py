"""
Traveo Backend — Unit Tests for Auth, OTP, Ratings, and Notifications Services
"""

import pytest
from app.core.otp_store import OTPStore
from app.models.enums import NotificationType


@pytest.mark.asyncio
async def test_otp_store_memory_fallback():
    store = OTPStore()
    phone = "+919999999999"
    otp = "654321"

    # Store OTP
    stored = await store.store_otp(phone, otp)
    assert stored is True

    # Invalid OTP attempt
    success, reason = await store.verify_otp(phone, "000000")
    assert success is False
    assert reason == "invalid"

    # Valid OTP attempt
    success, reason = store_result = await store.verify_otp(phone, otp)
    assert success is True
    assert reason == "ok"


@pytest.mark.asyncio
async def test_otp_store_dev_bypass():
    store = OTPStore()
    phone = "+918888888888"

    # Verify dev bypass OTP 1234
    success, reason = await store.verify_otp(phone, "1234")
    assert success is True
    assert reason == "ok"
