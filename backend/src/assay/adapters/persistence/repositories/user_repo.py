from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from assay.domain import EmailAddress, KycStatus, Money, User

from ..models import UserRow


@dataclass(slots=True)
class UserReadModel:
    """Read-only projection row materialised from the events stream."""

    user_id: UUID
    email: str
    kyc_status: str
    wallet_address: str | None
    available_balance: Decimal
    locked_balance: Decimal
    created_at: datetime


class UserRepository:
    """Reads and writes the `users` projection.

    The User aggregate carries authority; this repo just mirrors its state into
    the read model after the aggregate's events have been appended.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, user: User, *, password_hash: str | None = None) -> None:
        existing = await self._session.get(UserRow, user.user_id)
        if existing is None:
            row = UserRow(
                user_id=user.user_id,
                email=user.email.value,
                kyc_status=user.kyc_status.value,
                wallet_address=user.wallet_address,
                password_hash=password_hash,
                available_balance=user.available_balance.amount,
                locked_balance=user.locked_balance.amount,
            )
            self._session.add(row)
        else:
            existing.email = user.email.value
            existing.kyc_status = user.kyc_status.value
            existing.wallet_address = user.wallet_address
            if password_hash is not None:
                existing.password_hash = password_hash
            existing.available_balance = user.available_balance.amount
            existing.locked_balance = user.locked_balance.amount
        await self._session.flush()

    async def find(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserRow, user_id)
        if row is None:
            return None
        return _to_user(row)

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(UserRow).where(UserRow.email == email)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_user(row) if row else None

    async def read(self, user_id: UUID) -> UserReadModel | None:
        row = await self._session.get(UserRow, user_id)
        return _to_read_model(row) if row else None


def _to_user(row: UserRow) -> User:
    return User(
        user_id=row.user_id,
        email=EmailAddress(row.email),
        kyc_status=KycStatus(row.kyc_status),
        available_balance=Money(row.available_balance),
        locked_balance=Money(row.locked_balance),
        wallet_address=row.wallet_address,
    )


def _to_read_model(row: UserRow) -> UserReadModel:
    return UserReadModel(
        user_id=row.user_id,
        email=row.email,
        kyc_status=row.kyc_status,
        wallet_address=row.wallet_address,
        available_balance=row.available_balance,
        locked_balance=row.locked_balance,
        created_at=row.created_at,
    )
