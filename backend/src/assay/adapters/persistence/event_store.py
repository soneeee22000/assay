from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from assay.domain import DomainEvent

from .models import EventRow

_STREAM_TYPE_BY_EVENT_PREFIX: dict[str, str] = {
    "User": "user",
    "Kyc": "user",
    "Funds": "user",
    "Asset": "asset",
    "Escrow": "escrow",
    "VaultAttested": "escrow",
    "CertificateMinted": "escrow",
}


class ConcurrencyConflict(Exception):
    """Raised when an event append violates the (stream_id, version) unique constraint."""


@dataclass(slots=True)
class PersistedEvent:
    event_id: UUID
    stream_id: UUID
    stream_type: str
    version: int
    event_type: str
    payload: dict[str, Any]
    correlation_id: UUID
    ts: datetime


class EventStore:
    """Append-only event log over the single `events` table (ADR-003).

    Stream type is derived from the event class name; stream id is provided by
    the caller (typically the aggregate id). Versions are sequential per stream
    and enforced by a unique constraint at the DB layer — concurrent writers
    racing on the same aggregate will see one succeed and the other raise
    `ConcurrencyConflict`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        stream_id: UUID,
        events: list[DomainEvent],
        correlation_id: UUID | None = None,
    ) -> list[PersistedEvent]:
        if not events:
            return []
        starting_version = await self._next_version(stream_id)
        corr = correlation_id or uuid4()
        rows: list[EventRow] = []
        for offset, ev in enumerate(events):
            event_type = type(ev).__name__
            row = EventRow(
                event_id=ev.event_id,
                stream_id=stream_id,
                stream_type=_stream_type_of(event_type),
                version=starting_version + offset,
                event_type=event_type,
                payload=_serialise_payload(ev),
                correlation_id=corr,
                ts=ev.occurred_at,
            )
            rows.append(row)
            self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ConcurrencyConflict(
                f"concurrent append to stream {stream_id} (versions {starting_version}+)"
            ) from exc
        return [_to_persisted(r) for r in rows]

    async def load(self, stream_id: UUID) -> list[PersistedEvent]:
        stmt = select(EventRow).where(EventRow.stream_id == stream_id).order_by(EventRow.version)
        result = await self._session.execute(stmt)
        return [_to_persisted(row) for row in result.scalars().all()]

    async def export_window(self, *, frm: datetime, to: datetime) -> list[PersistedEvent]:
        stmt = (
            select(EventRow)
            .where(EventRow.ts >= frm, EventRow.ts < to)
            .order_by(EventRow.ts, EventRow.version)
        )
        result = await self._session.execute(stmt)
        return [_to_persisted(row) for row in result.scalars().all()]

    async def _next_version(self, stream_id: UUID) -> int:
        stmt = (
            select(EventRow.version)
            .where(EventRow.stream_id == stream_id)
            .order_by(EventRow.version.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        latest = result.scalar_one_or_none()
        return (latest or 0) + 1


def _stream_type_of(event_type: str) -> str:
    for prefix, stream in _STREAM_TYPE_BY_EVENT_PREFIX.items():
        if event_type.startswith(prefix):
            return stream
    return "unknown"


def _serialise_payload(ev: DomainEvent) -> dict[str, Any]:
    if not is_dataclass(ev):
        raise TypeError(f"event {type(ev).__name__} must be a dataclass")
    raw = asdict(ev)
    raw.pop("event_id", None)
    raw.pop("occurred_at", None)
    serialised: dict[str, Any] = json.loads(json.dumps(raw, default=_json_default))
    return serialised


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"cannot serialise {type(value).__name__}")


def _to_persisted(row: EventRow) -> PersistedEvent:
    return PersistedEvent(
        event_id=row.event_id,
        stream_id=row.stream_id,
        stream_type=row.stream_type,
        version=row.version,
        event_type=row.event_type,
        payload=row.payload,
        correlation_id=row.correlation_id,
        ts=row.ts,
    )
