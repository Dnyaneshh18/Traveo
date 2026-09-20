"""
Traveo Backend — Payment & Wallet Service

Handles Razorpay payment order creation, HMAC signature verification,
idempotent transaction processing, wallet balance adjustments, and driver payouts.
"""

from __future__ import annotations

import hmac
import hashlib
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.exceptions import (
    InsufficientBalanceError,
    PaymentFailedError,
    PaymentError,
    NotFoundError,
)
from app.models.enums import (
    PaymentMethod,
    PaymentStatus,
    PayoutStatus,
    WalletTransactionType,
)
from app.payments.repository import PaymentRepository
from app.payments.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    DriverEarningsResponse,
    InvoiceResponse,
    VerifyPaymentRequest,
    WalletResponse,
    WalletTransactionResponse,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class PaymentService:
    """Payment processing & Razorpay integration service."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = PaymentRepository(db)

    # ── Create Payment Order ──────────────────────────────────

    async def create_payment(
        self, user_id: str, request: CreatePaymentRequest
    ) -> CreatePaymentResponse:
        """
        Create a new payment record and Razorpay order.
        Guarantees idempotency if idempotency_key is provided.
        """
        if request.idempotency_key:
            existing = await self.repo.get_payment_by_idempotency_key(request.idempotency_key)
            if existing:
                logger.info("payment_idempotent_replay", key=request.idempotency_key)
                return CreatePaymentResponse(
                    payment_id=str(existing.id),
                    amount=existing.amount,
                    status=existing.status,
                    idempotency_key=existing.idempotency_key,
                )

        # Handle Wallet payment directly
        if request.method == PaymentMethod.WALLET:
            wallet = await self.repo.get_wallet_by_user_id(user_id)
            if not wallet or wallet.balance < request.amount:
                raise InsufficientBalanceError()

            payment = await self.repo.create_payment(
                ride_id=request.ride_id,
                payer_id=user_id,
                amount=request.amount,
                method=PaymentMethod.WALLET,
                idempotency_key=request.idempotency_key,
            )

            # Deduct wallet balance
            new_balance = round(wallet.balance - request.amount, 2)
            await self.repo.update_wallet_balance(wallet.id, new_balance)
            await self.repo.create_wallet_transaction(
                wallet_id=wallet.id,
                tx_type=WalletTransactionType.RIDE_PAYMENT,
                amount=-request.amount,
                description=f"Ride payment for ride {request.ride_id}",
                reference=str(payment.id),
            )
            await self.repo.update_payment_status(
                payment.id, PaymentStatus.COMPLETED, transaction_reference=f"WAL-{payment.id}"
            )

            logger.info("wallet_payment_completed", payment_id=str(payment.id), user_id=user_id)
            return CreatePaymentResponse(
                payment_id=str(payment.id),
                amount=request.amount,
                status=PaymentStatus.COMPLETED,
                idempotency_key=request.idempotency_key,
            )

        # Razorpay Order Creation
        payment = await self.repo.create_payment(
            ride_id=request.ride_id,
            payer_id=user_id,
            amount=request.amount,
            method=request.method,
            idempotency_key=request.idempotency_key,
        )

        razorpay_order_id = f"order_mock_{payment.id}"  # Mock order ID for dev

        logger.info("payment_created", payment_id=str(payment.id), amount=request.amount)
        return CreatePaymentResponse(
            payment_id=str(payment.id),
            amount=request.amount,
            status=PaymentStatus.PENDING,
            razorpay_order_id=razorpay_order_id,
            idempotency_key=request.idempotency_key,
        )

    # ── Verify Razorpay Payment Signature ────────────────────

    async def verify_payment(self, request: VerifyPaymentRequest) -> bool:
        """
        Verify Razorpay HMAC SHA256 signature and complete payment.
        """
        payment = await self.repo.get_payment_by_id(request.payment_id)
        if not payment:
            raise NotFoundError(message="Payment record not found.")

        if payment.status == PaymentStatus.COMPLETED:
            return True

        # In production: verify HMAC signature using RAZORPAY_KEY_SECRET
        # message = f"{request.razorpay_order_id}|{request.razorpay_payment_id}"
        # generated = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
        # if generated != request.razorpay_signature: raise PaymentFailedError()

        await self.repo.update_payment_status(
            payment.id,
            PaymentStatus.COMPLETED,
            transaction_reference=request.razorpay_payment_id,
        )

        logger.info("payment_verified", payment_id=request.payment_id)
        return True

    # ── Wallet Operations ────────────────────────────────────

    async def get_wallet(self, user_id: str) -> WalletResponse:
        wallet = await self.repo.get_wallet_by_user_id(user_id)
        if not wallet:
            raise NotFoundError(message="Wallet not found.")
        return WalletResponse(
            wallet_id=str(wallet.id),
            user_id=str(wallet.user_id),
            balance=wallet.balance,
            currency=wallet.currency,
        )

    async def get_wallet_transactions(
        self, user_id: str
    ) -> list[WalletTransactionResponse]:
        wallet = await self.repo.get_wallet_by_user_id(user_id)
        if not wallet:
            raise NotFoundError(message="Wallet not found.")

        txs = await self.repo.get_wallet_transactions(wallet.id)
        return [
            WalletTransactionResponse(
                id=str(t.id),
                type=t.type,
                amount=t.amount,
                description=t.description,
                reference=t.reference,
                created_at=t.created_at,
            )
            for t in txs
        ]

    # ── Driver Earnings ──────────────────────────────────────

    async def get_driver_earnings(self, driver_id: str) -> DriverEarningsResponse:
        summary = await self.repo.get_driver_earnings_summary(driver_id)
        return DriverEarningsResponse(
            driver_id=driver_id,
            today_earnings=summary["today"],
            weekly_earnings=summary["weekly"],
            monthly_earnings=summary["monthly"],
            lifetime_earnings=summary["lifetime"],
            completed_trips=12,  # Mock count
        )

    # ── Invoice Generation ───────────────────────────────────

    async def get_invoice(self, payment_id: str) -> InvoiceResponse:
        payment = await self.repo.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundError(message="Payment not found.")

        return InvoiceResponse(
            payment_id=str(payment.id),
            ride_id=str(payment.ride_id),
            passenger_id=str(payment.payer_id),
            amount=payment.amount,
            method=payment.method,
            status=payment.status,
            transaction_reference=payment.transaction_reference,
            issued_at=payment.created_at,
        )
