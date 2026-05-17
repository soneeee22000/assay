from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from assay.domain import Escrow, EscrowState, Money

from ..models import EscrowRow


@dataclass(slots=True)
class EscrowReadModel:
    escrow_id: UUID
    buyer_id: UUID
    seller_id: UUID
    asset_id: UUID
    amount_usdc: Decimal
    state: str
    opened_at: datetime
    locked_at: datetime | None
    attested_at: datetime | None
    minted_at: datetime | None
    released_at: datetime | None


_TIMESTAMP_COLUMN_BY_STATE: dict[EscrowState, str] = {
    EscrowState.PENDING: "opened_at",
    EscrowState.FUNDS_LOCKED: "locked_at",
    EscrowState.VAULT_ATTESTED: "attested_at",
    EscrowState.CERTIFICATE_MINTED: "minted_at",
    EscrowState.RELEASED: "released_at",
    EscrowState.CANCELLED: "cancelled_at",
    EscrowState.REFUNDED: "refunded_at",
}


class EscrowRepository:
    """Reads and writes the `escrows` projection.

    Every transition stamps the timestamp column matching the destination state,
    so the read model carries the full lifecycle timeline. The state column is
    a denormalised cache of the aggregate's current state.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, escrow: Escrow) -> None:
        existing = await self._session.get(EscrowRow, escrow.escrow_id)
        now = datetime.now(UTC)
        if existing is None:
            row = EscrowRow(
                escrow_id=escrow.escrow_id,
                buyer_id=escrow.buyer_id,
                seller_id=escrow.seller_id,
                asset_id=escrow.asset_id,
                amount_usdc=escrow.amount.amount,
                state=escrow.state.value,
                opened_at=now,
            )
            self._session.add(row)
        else:
            existing.state = escrow.state.value
            column = _TIMESTAMP_COLUMN_BY_STATE[escrow.state]
            if getattr(existing, column) is None:
                setattr(existing, column, now)
        await self._session.flush()

    async def find(self, escrow_id: UUID) -> Escrow | None:
        row = await self._session.get(EscrowRow, escrow_id)
        return _to_escrow(row) if row else None

    async def read(self, escrow_id: UUID) -> EscrowReadModel | None:
        row = await self._session.get(EscrowRow, escrow_id)
        return _to_read_model(row) if row else None


def _to_escrow(row: EscrowRow) -> Escrow:
    return Escrow(
        escrow_id=row.escrow_id,
        buyer_id=row.buyer_id,
        seller_id=row.seller_id,
        asset_id=row.asset_id,
        amount=Money(row.amount_usdc),
        state=EscrowState(row.state),
    )


def _to_read_model(row: EscrowRow) -> EscrowReadModel:
    return EscrowReadModel(
        escrow_id=row.escrow_id,
        buyer_id=row.buyer_id,
        seller_id=row.seller_id,
        asset_id=row.asset_id,
        amount_usdc=row.amount_usdc,
        state=row.state,
        opened_at=row.opened_at,
        locked_at=row.locked_at,
        attested_at=row.attested_at,
        minted_at=row.minted_at,
        released_at=row.released_at,
    )
