"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-11 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


USDC = sa.Numeric(20, 6)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("kyc_status", sa.String(16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("wallet_address", sa.String(64), nullable=True),
        sa.Column("password_hash", sa.String(256), nullable=True),
        sa.Column("available_balance", USDC, nullable=False, server_default=sa.text("0")),
        sa.Column("locked_balance", USDC, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "kyc_status in ('PENDING','APPROVED','REJECTED')", name="ck_users_kyc_status"
        ),
        sa.CheckConstraint("available_balance >= 0", name="ck_users_available_nonneg"),
        sa.CheckConstraint("locked_balance >= 0", name="ck_users_locked_nonneg"),
    )

    op.create_table(
        "assets",
        sa.Column("asset_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("grade", sa.String(32), nullable=True),
        sa.Column("weight_troy_oz", sa.Numeric(10, 3), nullable=True),
        sa.Column("lab_cert_number", sa.String(128), nullable=False, unique=True),
        sa.Column("photo_ipfs_hash", sa.String(128), nullable=True),
        sa.Column("vault_location", sa.String(64), nullable=False),
        sa.Column(
            "owner_user_id", PgUUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "escrows",
        sa.Column("escrow_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("buyer_id", PgUUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column(
            "seller_id", PgUUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column(
            "asset_id", PgUUID(as_uuid=True), sa.ForeignKey("assets.asset_id"), nullable=False
        ),
        sa.Column("amount_usdc", USDC, nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("minted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state in ('PENDING','FUNDS_LOCKED','VAULT_ATTESTED',"
            "'CERTIFICATE_MINTED','RELEASED','CANCELLED','REFUNDED')",
            name="ck_escrows_state",
        ),
        sa.CheckConstraint("amount_usdc > 0", name="ck_escrows_amount_positive"),
    )
    op.create_index("idx_escrows_buyer", "escrows", ["buyer_id"])
    op.create_index("idx_escrows_seller", "escrows", ["seller_id"])
    op.create_index("idx_escrows_state", "escrows", ["state"])

    op.create_table(
        "certificates",
        sa.Column("certificate_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "asset_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("assets.asset_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "owner_user_id", PgUUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column("token_id", sa.Numeric(78, 0), nullable=False),
        sa.Column("contract_address", sa.String(64), nullable=False),
        sa.Column("tx_hash", sa.String(66), nullable=False),
        sa.Column("ipfs_metadata_hash", sa.String(128), nullable=False),
        sa.Column("minted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("contract_address", "token_id", name="uq_cert_contract_token"),
    )

    op.create_table(
        "events",
        sa.Column("event_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("stream_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("stream_type", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("correlation_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("stream_id", "version", name="uq_events_stream_version"),
    )
    op.create_index("idx_events_stream", "events", ["stream_id", "version"])
    op.create_index("idx_events_correlation", "events", ["correlation_id"])
    op.create_index("idx_events_ts", "events", ["ts"])

    op.create_table(
        "vault_attestations",
        sa.Column("attestation_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "escrow_id", PgUUID(as_uuid=True), sa.ForeignKey("escrows.escrow_id"), nullable=False
        ),
        sa.Column("vault_operator_id", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(128), nullable=False),
        sa.Column("nonce", sa.String(128), nullable=False),
        sa.Column("signature", sa.String(256), nullable=False),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("vault_operator_id", "nonce", name="uq_vault_op_nonce"),
    )

    op.create_table(
        "ledger_entries",
        sa.Column("entry_id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "event_id", PgUUID(as_uuid=True), sa.ForeignKey("events.event_id"), nullable=False
        ),
        sa.Column("account_id", sa.String(128), nullable=False),
        sa.Column("direction", sa.String(1), nullable=False),
        sa.Column("amount_usdc", USDC, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("direction in ('D','C')", name="ck_ledger_direction"),
        sa.CheckConstraint("amount_usdc > 0", name="ck_ledger_amount_positive"),
    )
    op.create_index("idx_ledger_account", "ledger_entries", ["account_id", "ts"])
    op.create_index("idx_ledger_event", "ledger_entries", ["event_id"])


def downgrade() -> None:
    op.drop_index("idx_ledger_event", table_name="ledger_entries")
    op.drop_index("idx_ledger_account", table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_table("vault_attestations")
    op.drop_index("idx_events_ts", table_name="events")
    op.drop_index("idx_events_correlation", table_name="events")
    op.drop_index("idx_events_stream", table_name="events")
    op.drop_table("events")
    op.drop_table("certificates")
    op.drop_index("idx_escrows_state", table_name="escrows")
    op.drop_index("idx_escrows_seller", table_name="escrows")
    op.drop_index("idx_escrows_buyer", table_name="escrows")
    op.drop_table("escrows")
    op.drop_table("assets")
    op.drop_table("users")
