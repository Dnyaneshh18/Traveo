"""
Traveo Backend — Payments, Wallet & Earnings Router

HTTP endpoints for payment creation, Razorpay verification, wallet management,
and driver earnings reporting.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies import get_current_user_id, RequireDriver
from app.payments.schemas import CreatePaymentRequest, VerifyPaymentRequest
from app.payments.service import PaymentService
from app.schemas.base import success_response

router = APIRouter()


def _get_payment_service(db: AsyncSession = Depends(get_db_session)) -> PaymentService:
    return PaymentService(db)


# ── POST /payments/create ───────────────────────────────────
@router.post("/create")
async def create_payment(
    request: CreatePaymentRequest,
    user_id: str = Depends(get_current_user_id),
    service: PaymentService = Depends(_get_payment_service),
):
    """
    Create a new payment order (Razorpay or Wallet).
    """
    result = await service.create_payment(user_id, request)
    return success_response(
        data=result.model_dump(),
        message="Payment order created successfully.",
    )


# ── POST /payments/verify ───────────────────────────────────
@router.post("/verify")
async def verify_payment(
    request: VerifyPaymentRequest,
    service: PaymentService = Depends(_get_payment_service),
):
    """
    Verify Razorpay payment signature.
    """
    success = await service.verify_payment(request)
    return success_response(
        data={"verified": success},
        message="Payment verified successfully.",
    )


# ── GET /payments/{payment_id}/invoice ──────────────────────
@router.get("/{payment_id}/invoice")
async def get_invoice(
    payment_id: str,
    service: PaymentService = Depends(_get_payment_service),
):
    """
    Get digital invoice for a payment.
    """
    result = await service.get_invoice(payment_id)
    return success_response(
        data=result.model_dump(),
        message="Invoice retrieved successfully.",
    )


# ── GET /wallet ──────────────────────────────────────────────
@router.get("/wallet/balance")
async def get_wallet_balance(
    user_id: str = Depends(get_current_user_id),
    service: PaymentService = Depends(_get_payment_service),
):
    """
    Get user's wallet balance.
    """
    result = await service.get_wallet(user_id)
    return success_response(
        data=result.model_dump(),
        message="Wallet balance retrieved.",
    )


# ── GET /wallet/transactions ─────────────────────────────────
@router.get("/wallet/transactions")
async def get_wallet_transactions(
    user_id: str = Depends(get_current_user_id),
    service: PaymentService = Depends(_get_payment_service),
):
    """
    Get user's wallet transaction history.
    """
    results = await service.get_wallet_transactions(user_id)
    return success_response(
        data=[r.model_dump() for r in results],
        message="Wallet transaction history retrieved.",
    )


# ── GET /driver/earnings ────────────────────────────────────
@router.get("/driver/earnings")
async def get_driver_earnings(
    user_id: str = Depends(RequireDriver),
    service: PaymentService = Depends(_get_payment_service),
):
    """
    Get driver earnings breakdown (today, weekly, monthly, lifetime).
    """
    driver_id = user_id[0] if isinstance(user_id, tuple) else user_id
    result = await service.get_driver_earnings(driver_id)
    return success_response(
        data=result.model_dump(),
        message="Driver earnings retrieved successfully.",
    )
