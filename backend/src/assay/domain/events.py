from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base class for every domain event.

    Events are append-only facts about what has happened. They are immutable
    once created. Application code persists them via the event store; aggregates
    derive state by replaying them.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True, kw_only=True)
class UserRegistered(DomainEvent):
    user_id: UUID
    email: str


@dataclass(frozen=True, slots=True, kw_only=True)
class KycApproved(DomainEvent):
    user_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class KycRejected(DomainEvent):
    user_id: UUID
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class FundsDeposited(DomainEvent):
    user_id: UUID
    amount: Decimal
    tx_hash: str


@dataclass(frozen=True, slots=True, kw_only=True)
class FundsWithdrawn(DomainEvent):
    user_id: UUID
    amount: Decimal
    tx_hash: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AssetRegistered(DomainEvent):
    asset_id: UUID
    asset_type: str
    lab_cert_number: str
    vault_location: str
    owner_user_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class EscrowOpened(DomainEvent):
    escrow_id: UUID
    buyer_id: UUID
    seller_id: UUID
    asset_id: UUID
    amount: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class FundsLocked(DomainEvent):
    escrow_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class VaultAttested(DomainEvent):
    escrow_id: UUID
    attestation_id: UUID
    payload_hash: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CertificateMinted(DomainEvent):
    escrow_id: UUID
    certificate_id: UUID
    token_id: int
    tx_hash: str
    ipfs_hash: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EscrowReleased(DomainEvent):
    escrow_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class EscrowCancelled(DomainEvent):
    escrow_id: UUID
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EscrowRefunded(DomainEvent):
    escrow_id: UUID
    amount: Decimal
    reason: str
