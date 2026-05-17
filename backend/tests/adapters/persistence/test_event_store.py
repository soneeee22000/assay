from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from assay.adapters.persistence import EventStore
from assay.adapters.persistence.event_store import ConcurrencyConflict
from assay.domain import EscrowOpened, FundsLocked, UserRegistered, VaultAttested

pytestmark = pytest.mark.asyncio


class TestAppend:
    async def test_appends_single_event_at_version_1(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        ev = UserRegistered(user_id=stream_id, email="a@example.com")

        persisted = await store.append(stream_id=stream_id, events=[ev])

        assert len(persisted) == 1
        assert persisted[0].version == 1
        assert persisted[0].event_type == "UserRegistered"
        assert persisted[0].stream_type == "user"
        assert persisted[0].payload["email"] == "a@example.com"

    async def test_appends_two_events_with_sequential_versions(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        events = [
            EscrowOpened(
                escrow_id=stream_id,
                buyer_id=uuid4(),
                seller_id=uuid4(),
                asset_id=uuid4(),
                amount=Decimal("12.345678"),
            ),
            FundsLocked(escrow_id=stream_id),
        ]

        persisted = await store.append(stream_id=stream_id, events=events)

        assert [p.version for p in persisted] == [1, 2]
        assert [p.event_type for p in persisted] == ["EscrowOpened", "FundsLocked"]

    async def test_continues_versioning_across_calls(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        await store.append(
            stream_id=stream_id,
            events=[UserRegistered(user_id=stream_id, email="a@example.com")],
        )
        second = await store.append(
            stream_id=stream_id,
            events=[UserRegistered(user_id=stream_id, email="a@example.com")],
        )
        assert second[0].version == 2

    async def test_empty_events_is_noop(self, session: AsyncSession) -> None:
        store = EventStore(session)
        result = await store.append(stream_id=uuid4(), events=[])
        assert result == []

    async def test_correlation_id_shared_across_batch(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        correlation_id = uuid4()
        events = [
            EscrowOpened(
                escrow_id=stream_id,
                buyer_id=uuid4(),
                seller_id=uuid4(),
                asset_id=uuid4(),
                amount=Decimal("1.0"),
            ),
            FundsLocked(escrow_id=stream_id),
        ]

        persisted = await store.append(
            stream_id=stream_id, events=events, correlation_id=correlation_id
        )

        assert all(p.correlation_id == correlation_id for p in persisted)


class TestConcurrencyConflict:
    async def test_two_writers_at_same_version_raises(
        self,
        engine,
        sessions,
    ) -> None:
        stream_id = uuid4()

        async with sessions() as s1, sessions() as s2:
            store1 = EventStore(s1)
            store2 = EventStore(s2)

            await store1.append(
                stream_id=stream_id,
                events=[UserRegistered(user_id=stream_id, email="a@example.com")],
            )
            await store2.append(
                stream_id=stream_id,
                events=[UserRegistered(user_id=stream_id, email="b@example.com")],
            )

            await s1.commit()
            with pytest.raises(ConcurrencyConflict):
                await s2.commit()


class TestLoad:
    async def test_returns_events_in_version_order(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        await store.append(
            stream_id=stream_id,
            events=[
                EscrowOpened(
                    escrow_id=stream_id,
                    buyer_id=uuid4(),
                    seller_id=uuid4(),
                    asset_id=uuid4(),
                    amount=Decimal("1.0"),
                ),
                FundsLocked(escrow_id=stream_id),
                VaultAttested(
                    escrow_id=stream_id,
                    attestation_id=uuid4(),
                    payload_hash="hash",
                ),
            ],
        )

        loaded = await store.load(stream_id)

        assert [e.version for e in loaded] == [1, 2, 3]
        assert [e.event_type for e in loaded] == [
            "EscrowOpened",
            "FundsLocked",
            "VaultAttested",
        ]

    async def test_returns_empty_for_unknown_stream(self, session: AsyncSession) -> None:
        store = EventStore(session)
        assert await store.load(uuid4()) == []


class TestExportWindow:
    async def test_includes_events_within_window(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        before = datetime.now(UTC) - timedelta(seconds=1)
        await store.append(
            stream_id=stream_id,
            events=[UserRegistered(user_id=stream_id, email="a@example.com")],
        )
        after = datetime.now(UTC) + timedelta(seconds=1)

        window = await store.export_window(frm=before, to=after)

        assert any(e.stream_id == stream_id for e in window)

    async def test_excludes_events_outside_window(self, session: AsyncSession) -> None:
        store = EventStore(session)
        stream_id = uuid4()
        await store.append(
            stream_id=stream_id,
            events=[UserRegistered(user_id=stream_id, email="a@example.com")],
        )
        future = datetime.now(UTC) + timedelta(days=1)
        far_future = future + timedelta(days=1)

        window = await store.export_window(frm=future, to=far_future)

        assert window == []
