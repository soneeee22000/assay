from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

USDC_NUMERIC = Numeric(20, 6)


class Base(DeclarativeBase):
    """Single declarative base for every persistence model in the platform."""


class EventRow(Base):
    """The append-only event store. Single table per ADR-003."""

    __tablename__ = "events"

    event_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    stream_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    stream_type: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("stream_id", "version", name="uq_events_stream_version"),
        Index("idx_events_stream", "stream_id", "version"),
        Index("idx_events_correlation", "correlation_id"),
        Index("idx_events_ts", "ts"),
    )


class UserRow(Base):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    kyc_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'PENDING'")
    )
    wallet_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    available_balance: Mapped[Decimal] = mapped_column(
        USDC_NUMERIC, nullable=False, server_default=text("0")
    )
    locked_balance: Mapped[Decimal] = mapped_column(
        USDC_NUMERIC, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "kyc_status in ('PENDING','APPROVED','REJECTED')",
            name="ck_users_kyc_status",
        ),
        CheckConstraint("available_balance >= 0", name="ck_users_available_nonneg"),
        CheckConstraint("locked_balance >= 0", name="ck_users_locked_nonneg"),
    )


class AssetRow(Base):
    __tablename__ = "assets"

    asset_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    weight_troy_oz: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    lab_cert_number: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    photo_ipfs_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vault_location: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class EscrowRow(Base):
    __tablename__ = "escrows"

    escrow_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    buyer_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    seller_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    asset_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=False
    )
    amount_usdc: Mapped[Decimal] = mapped_column(USDC_NUMERIC, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    minted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "state in ('PENDING','FUNDS_LOCKED','VAULT_ATTESTED',"
            "'CERTIFICATE_MINTED','RELEASED','CANCELLED','REFUNDED')",
            name="ck_escrows_state",
        ),
        CheckConstraint("amount_usdc > 0", name="ck_escrows_amount_positive"),
        Index("idx_escrows_buyer", "buyer_id"),
        Index("idx_escrows_seller", "seller_id"),
        Index("idx_escrows_state", "state"),
    )


class CertificateRow(Base):
    __tablename__ = "certificates"

    certificate_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("assets.asset_id"),
        unique=True,
        nullable=False,
    )
    owner_user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    token_id: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False)
    contract_address: Mapped[str] = mapped_column(String(64), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    ipfs_metadata_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    minted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("contract_address", "token_id", name="uq_cert_contract_token"),
    )


class VaultAttestationRow(Base):
    __tablename__ = "vault_attestations"

    attestation_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    escrow_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("escrows.escrow_id"), nullable=False
    )
    vault_operator_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    signature: Mapped[str] = mapped_column(String(256), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("vault_operator_id", "nonce", name="uq_vault_op_nonce"),)


class LedgerEntryRow(Base):
    __tablename__ = "ledger_entries"

    entry_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    event_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("events.event_id"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    direction: Mapped[str] = mapped_column(String(1), nullable=False)
    amount_usdc: Mapped[Decimal] = mapped_column(USDC_NUMERIC, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("direction in ('D','C')", name="ck_ledger_direction"),
        CheckConstraint("amount_usdc > 0", name="ck_ledger_amount_positive"),
        Index("idx_ledger_account", "account_id", "ts"),
        Index("idx_ledger_event", "event_id"),
    )
