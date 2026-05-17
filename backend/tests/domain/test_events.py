from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from assay.domain import DomainEvent, EscrowOpened, UserRegistered


class TestDomainEventDefaults:
    def test_event_id_is_unique_per_event(self) -> None:
        a = UserRegistered(user_id=uuid4(), email="a@example.com")
        b = UserRegistered(user_id=uuid4(), email="b@example.com")
        assert a.event_id != b.event_id

    def test_occurred_at_is_timezone_aware_utc(self) -> None:
        ev = UserRegistered(user_id=uuid4(), email="a@example.com")
        assert ev.occurred_at.tzinfo is not None
        assert ev.occurred_at.tzinfo.utcoffset(ev.occurred_at) == timedelta(0)

    def test_occurred_at_is_recent(self) -> None:
        ev = UserRegistered(user_id=uuid4(), email="a@example.com")
        delta = datetime.now(UTC) - ev.occurred_at
        assert abs(delta.total_seconds()) < 1.0


class TestEventImmutability:
    def test_cannot_mutate_event_field(self) -> None:
        ev = UserRegistered(user_id=uuid4(), email="a@example.com")
        with pytest.raises(FrozenInstanceError):
            ev.email = "evil@example.com"  # type: ignore[misc]


class TestEventCarriesRequiredFields:
    def test_escrow_opened_carries_participants_and_amount(self) -> None:
        buyer, seller, asset, escrow = uuid4(), uuid4(), uuid4(), uuid4()
        ev = EscrowOpened(
            escrow_id=escrow,
            buyer_id=buyer,
            seller_id=seller,
            asset_id=asset,
            amount=Decimal("12.345678"),
        )
        assert ev.escrow_id == escrow
        assert ev.buyer_id == buyer
        assert ev.seller_id == seller
        assert ev.asset_id == asset
        assert ev.amount == Decimal("12.345678")


class TestDomainEventBaseDirectInstantiation:
    def test_base_class_is_constructible_with_defaults(self) -> None:
        ev = DomainEvent()
        assert ev.event_id is not None
        assert ev.occurred_at is not None
