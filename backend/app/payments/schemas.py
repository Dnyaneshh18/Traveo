"""
Traveo Backend — Payment & Wallet Schemas
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import PaymentMethod, PaymentStatus, WalletTransactionType


# ── Payment Models ───────────────────────────────────────────

class CreatePaymentRequest(BaseModel):
    """POST /api/v1/payments/create"""

    ride_id: str
    amount: float = Field(gt=0.0)
    method: PaymentMethod
    idempotency_key: str | None = None


class CreatePaymentResponse(BaseModel):
    payment_id: str
    amount: float
    status: PaymentStatus
    razorpay_order_id: str | None = None
    idempotency_key: str | None = None


class VerifyPaymentRequest(BaseModel):
    """POST /api/v1/payments/verify"""

    payment_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class InvoiceResponse(BaseModel):
    """GET /api/v1/payments/{payment_id}/invoice"""

    payment_id: str
    ride_id: str
    passenger_id: str
    amount: float
    method: PaymentMethod | None
    status: PaymentStatus
    transaction_reference: str | None
    issued_at: datetime


# ── Wallet Models ────────────────────────────────────────────

class WalletResponse(BaseModel):
    wallet_id: str
    user_id: str
    balance: float
    currency: str


class WalletTransactionResponse(BaseModel):
    id: str
    type: WalletTransactionType
    amount: float
    description: str | None
    reference: str | None
    created_at: datetime


class AddWalletFundsRequest(BaseModel):
    amount: float = Field(gt=0.0, le=10000.0)
    payment_method: PaymentMethod = PaymentMethod.UPI


# ── Driver Earnings Models ────────────────────────────────────

class DriverEarningsResponse(BaseModel):
    driver_id: str
    today_earnings: float
    weekly_earnings: float
    monthly_earnings: float
    lifetime_earnings: float
    completed_trips: int
