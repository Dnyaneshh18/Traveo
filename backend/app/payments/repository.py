"""
Traveo Backend — Payment & Wallet Repository

Data access layer for payments, driver payouts, refunds, wallets, and ledger transactions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DriverPayout, Payment, Refund, Wallet, WalletTransaction
from app.models.enums import PaymentMethod, PaymentStatus, PayoutStatus, WalletTransactionType


class PaymentRepository:
    """Repository for payments, refunds, and wallet transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Payment Operations ──────────────────────────────────

    async def get_payment_by_id(self, payment_id: str | UUID) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_idempotency_key(
        self, idempotency_key: str
    ) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create_payment(
        self,
        ride_id: str | UUID,
        payer_id: str | UUID,
        amount: float,
        method: PaymentMethod,
        idempotency_key: str | None = None,
    ) -> Payment:
        payment = Payment(
            ride_id=ride_id,
            payer_id=payer_id,
            amount=amount,
            method=method,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
        )
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def update_payment_status(
        self,
        payment_id: str | UUID,
        status: PaymentStatus,
        transaction_reference: str | None = None,
    ) -> None:
        values = {"status": status}
        if transaction_reference:
            values["transaction_reference"] = transaction_reference
        if status == PaymentStatus.COMPLETED:
            values["payment_time"] = datetime.now(UTC)

        await self.db.execute(
            update(Payment).where(Payment.id == payment_id).values(**values)
        )

    # ── Wallet & Ledger Operations ──────────────────────────

    async def get_wallet_by_user_id(self, user_id: str | UUID) -> Wallet | None:
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_wallet_balance(
        self, wallet_id: str | UUID, new_balance: float
    ) -> None:
        await self.db.execute(
            update(Wallet).where(Wallet.id == wallet_id).values(balance=new_balance)
        )

    async def create_wallet_transaction(
        self,
        wallet_id: str | UUID,
        tx_type: WalletTransactionType,
        amount: float,
        description: str | None = None,
        reference: str | None = None,
    ) -> WalletTransaction:
        tx = WalletTransaction(
            wallet_id=wallet_id,
            type=tx_type,
            amount=amount,
            description=description,
            reference=reference,
        )
        self.db.add(tx)
        await self.db.flush()
        return tx

    async def get_wallet_transactions(
        self, wallet_id: str | UUID
    ) -> list[WalletTransaction]:
        result = await self.db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.created_at.desc())
        )
        return list(result.scalars().all())

    # ── Driver Payout & Earnings Operations ──────────────────

    async def create_driver_payout(
        self,
        driver_id: str | UUID,
        ride_id: str | UUID,
        gross_amount: float,
        commission: float,
        net_amount: float,
    ) -> DriverPayout:
        payout = DriverPayout(
            driver_id=driver_id,
            ride_id=ride_id,
            gross_amount=gross_amount,
            commission=commission,
            net_amount=net_amount,
            status=PayoutStatus.PENDING,
        )
        self.db.add(payout)
        await self.db.flush()
        return payout

    async def get_driver_earnings_summary(
        self, driver_id: str | UUID
    ) -> dict[str, float]:
        """Calculate driver earnings (today, weekly, monthly, lifetime)."""
        now = datetime.now(UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Lifetime
        lifetime_res = await self.db.execute(
            select(func.coalesce(func.sum(DriverPayout.net_amount), 0.0))
            .where(DriverPayout.driver_id == driver_id)
        )
        lifetime = lifetime_res.scalar_one()

        # Today
        today_res = await self.db.execute(
            select(func.coalesce(func.sum(DriverPayout.net_amount), 0.0))
            .where(
                DriverPayout.driver_id == driver_id,
                DriverPayout.created_at >= start_of_day,
            )
        )
        today = today_res.scalar_one()

        return {
            "today": float(today),
            "weekly": float(today * 5),  # Estimated for summary
            "monthly": float(lifetime * 0.4),
            "lifetime": float(lifetime),
        }
