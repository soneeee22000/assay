from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from assay.adapters.persistence import EscrowRepository, UserRepository
from assay.adapters.persistence.models import AssetRow
from assay.domain import (
    EmailAddress,
    Escrow,
    EscrowState,
    KycStatus,
    Money,
    TxHash,
    User,
)

pytestmark = pytest.mark.asyncio


class TestUserRepository:
    async def test_upsert_then_find(self, session: AsyncSession) -> None:
        repo = UserRepository(session)
        user = User.register(
            user_id=uuid4(),
            email=EmailAddress("alice@example.com"),
        )
        await repo.upsert(user)
        await session.commit()

        loaded = await repo.find(user.user_id)

        assert loaded is not None
        assert loaded.email.value == "alice@example.com"
        assert loaded.kyc_status == KycStatus.PENDING
        assert loaded.available_balance.is_zero()

    async def test_upsert_updates_balance_after_kyc_and_deposit(
        self, session: AsyncSession
    ) -> None:
        repo = UserRepository(session)
        user = User.register(user_id=uuid4(), email=EmailAddress("bob@example.com"))
        user.approve_kyc()
        user.deposit(Money(Decimal("125.0")), TxHash("0x" + "ab" * 32))
        await repo.upsert(user)
        await session.commit()

        loaded = await repo.find(user.user_id)

        assert loaded is not None
        assert loaded.kyc_status == KycStatus.APPROVED
        assert loaded.available_balance.amount == Decimal("125.000000")

    async def test_find_by_email(self, session: AsyncSession) -> None:
        repo = UserRepository(session)
        user = User.register(user_id=uuid4(), email=EmailAddress("carol@example.com"))
        await repo.upsert(user)
        await session.commit()

        loaded = await repo.find_by_email("carol@example.com")

        assert loaded is not None
        assert loaded.user_id == user.user_id

    async def test_find_unknown_returns_none(self, session: AsyncSession) -> None:
        repo = UserRepository(session)
        assert await repo.find(uuid4()) is None

    async def test_read_returns_projection(self, session: AsyncSession) -> None:
        repo = UserRepository(session)
        user = User.register(user_id=uuid4(), email=EmailAddress("dave@example.com"))
        await repo.upsert(user)
        await session.commit()

        view = await repo.read(user.user_id)

        assert view is not None
        assert view.email == "dave@example.com"
        assert view.kyc_status == "PENDING"


class TestEscrowRepository:
    async def test_upsert_pending_then_funds_locked_stamps_timestamps(
        self, session: AsyncSession
    ) -> None:
        buyer = await _make_user(session, "buyer@example.com")
        seller = await _make_user(session, "seller@example.com")
        asset = await _make_asset(session, owner_id=seller.user_id)
        await session.commit()

        repo = EscrowRepository(session)
        escrow = Escrow.open(
            escrow_id=uuid4(),
            buyer_id=buyer.user_id,
            seller_id=seller.user_id,
            asset_id=asset.asset_id,
            amount=Money(Decimal("100.0")),
        )
        await repo.upsert(escrow)
        await session.commit()

        first = await repo.read(escrow.escrow_id)
        assert first is not None
        assert first.state == "PENDING"
        assert first.opened_at is not None
        assert first.locked_at is None

        escrow.lock_funds()
        await repo.upsert(escrow)
        await session.commit()

        second = await repo.read(escrow.escrow_id)
        assert second is not None
        assert second.state == "FUNDS_LOCKED"
        assert second.locked_at is not None

    async def test_find_reconstructs_escrow_aggregate(self, session: AsyncSession) -> None:
        buyer = await _make_user(session, "x@example.com")
        seller = await _make_user(session, "y@example.com")
        asset = await _make_asset(session, owner_id=seller.user_id)
        await session.commit()

        repo = EscrowRepository(session)
        escrow = Escrow.open(
            escrow_id=uuid4(),
            buyer_id=buyer.user_id,
            seller_id=seller.user_id,
            asset_id=asset.asset_id,
            amount=Money(Decimal("42.0")),
        )
        await repo.upsert(escrow)
        await session.commit()

        loaded = await repo.find(escrow.escrow_id)
        assert loaded is not None
        assert loaded.amount.amount == Decimal("42.000000")
        assert loaded.state == EscrowState.PENDING


async def _make_user(session: AsyncSession, email: str) -> User:
    repo = UserRepository(session)
    user = User.register(user_id=uuid4(), email=EmailAddress(email))
    await repo.upsert(user)
    return user


async def _make_asset(session: AsyncSession, *, owner_id) -> AssetRow:
    row = AssetRow(
        asset_id=uuid4(),
        asset_type="gold-bar",
        lab_cert_number=f"LBMA-TEST-{uuid4().hex[:8]}",
        vault_location="ZUR-A",
        owner_user_id=owner_id,
    )
    session.add(row)
    await session.flush()
    return row
