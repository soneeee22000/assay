from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from assay.adapters.auth.passwords import hash_password, verify_password
from assay.adapters.chain import ChainClient
from assay.adapters.persistence import (
    EscrowRepository,
    EventStore,
    UserRepository,
)
from assay.adapters.persistence.models import (
    AssetRow,
    CertificateRow,
    UserRow,
    VaultAttestationRow,
)
from assay.domain import (
    Asset,
    EmailAddress,
    Escrow,
    EscrowState,
    InvalidEscrowParticipants,
    IpfsHash,
    Money,
    TokenId,
    TxHash,
    User,
)


class AuthenticationError(Exception):
    """Login failed: unknown user or wrong password."""


class NotFoundError(Exception):
    """A required record was not found in the read model."""


class WrongStateError(Exception):
    """Operation rejected because the aggregate is not in the required state."""


@dataclass(slots=True, frozen=True)
class RegisterUserInput:
    email: str
    password: str
    wallet_address: str | None = None


@dataclass(slots=True, frozen=True)
class LoginResult:
    user_id: UUID
    is_admin: bool


async def register_user(
    session: AsyncSession,
    inp: RegisterUserInput,
    *,
    correlation_id: UUID,
) -> User:
    user = User.register(
        user_id=uuid4(),
        email=EmailAddress(inp.email),
        wallet_address=inp.wallet_address,
    )
    repo = UserRepository(session)
    await repo.upsert(user, password_hash=hash_password(inp.password))
    await EventStore(session).append(
        stream_id=user.user_id,
        events=user.pull_events(),
        correlation_id=correlation_id,
    )
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> LoginResult:
    stmt = select(UserRow).where(UserRow.email == email)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None or row.password_hash is None:
        raise AuthenticationError("unknown user or no password set")
    if not verify_password(password, row.password_hash):
        raise AuthenticationError("password mismatch")
    return LoginResult(user_id=row.user_id, is_admin=row.kyc_status == "APPROVED")


async def approve_kyc(session: AsyncSession, *, user_id: UUID, correlation_id: UUID) -> User:
    repo = UserRepository(session)
    user = await repo.find(user_id)
    if user is None:
        raise NotFoundError(f"user {user_id} not found")
    user.approve_kyc()
    await repo.upsert(user)
    await EventStore(session).append(
        stream_id=user.user_id,
        events=user.pull_events(),
        correlation_id=correlation_id,
    )
    return user


async def deposit_funds(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount: Money,
    tx_hash: TxHash,
    correlation_id: UUID,
) -> User:
    repo = UserRepository(session)
    user = await repo.find(user_id)
    if user is None:
        raise NotFoundError(f"user {user_id} not found")
    user.deposit(amount, tx_hash)
    await repo.upsert(user)
    await EventStore(session).append(
        stream_id=user.user_id,
        events=user.pull_events(),
        correlation_id=correlation_id,
    )
    return user


@dataclass(slots=True, frozen=True)
class RegisterAssetInput:
    asset_type: str
    lab_cert_number: str
    vault_location: str
    owner_user_id: UUID
    grade: str | None = None
    weight_troy_oz: Decimal | None = None
    photo_ipfs_hash: str | None = None


async def register_asset(
    session: AsyncSession, inp: RegisterAssetInput, *, correlation_id: UUID
) -> Asset:
    asset = Asset.register(
        asset_id=uuid4(),
        asset_type=inp.asset_type,
        lab_cert_number=inp.lab_cert_number,
        vault_location=inp.vault_location,
        owner_user_id=inp.owner_user_id,
        grade=inp.grade,
        weight_troy_oz=inp.weight_troy_oz,
        photo_ipfs_hash=IpfsHash(inp.photo_ipfs_hash) if inp.photo_ipfs_hash else None,
    )
    row = AssetRow(
        asset_id=asset.asset_id,
        asset_type=asset.asset_type,
        grade=asset.grade,
        weight_troy_oz=asset.weight_troy_oz,
        lab_cert_number=asset.lab_cert_number,
        photo_ipfs_hash=asset.photo_ipfs_hash.value if asset.photo_ipfs_hash else None,
        vault_location=asset.vault_location,
        owner_user_id=asset.owner_user_id,
    )
    session.add(row)
    await session.flush()
    await EventStore(session).append(
        stream_id=asset.asset_id,
        events=asset.pull_events(),
        correlation_id=correlation_id,
    )
    return asset


@dataclass(slots=True, frozen=True)
class OpenEscrowInput:
    buyer_id: UUID
    seller_id: UUID
    asset_id: UUID
    amount: Money


async def open_escrow(
    session: AsyncSession, inp: OpenEscrowInput, *, correlation_id: UUID
) -> Escrow:
    asset_row = await session.get(AssetRow, inp.asset_id)
    if asset_row is None:
        raise NotFoundError(f"asset {inp.asset_id} not found")
    if asset_row.owner_user_id != inp.seller_id:
        raise InvalidEscrowParticipants("seller is not the asset owner")
    repo = EscrowRepository(session)
    escrow = Escrow.open(
        escrow_id=uuid4(),
        buyer_id=inp.buyer_id,
        seller_id=inp.seller_id,
        asset_id=inp.asset_id,
        amount=inp.amount,
    )
    await repo.upsert(escrow)
    await EventStore(session).append(
        stream_id=escrow.escrow_id,
        events=escrow.pull_events(),
        correlation_id=correlation_id,
    )
    return escrow


async def lock_funds(session: AsyncSession, *, escrow_id: UUID, correlation_id: UUID) -> Escrow:
    escrow_repo = EscrowRepository(session)
    user_repo = UserRepository(session)
    escrow = await escrow_repo.find(escrow_id)
    if escrow is None:
        raise NotFoundError(f"escrow {escrow_id} not found")
    buyer = await user_repo.find(escrow.buyer_id)
    if buyer is None:
        raise NotFoundError(f"buyer {escrow.buyer_id} not found")

    buyer.lock_funds(escrow.amount)
    escrow.lock_funds()

    await user_repo.upsert(buyer)
    await escrow_repo.upsert(escrow)
    event_store = EventStore(session)
    await event_store.append(
        stream_id=buyer.user_id,
        events=buyer.pull_events(),
        correlation_id=correlation_id,
    )
    await event_store.append(
        stream_id=escrow.escrow_id,
        events=escrow.pull_events(),
        correlation_id=correlation_id,
    )
    return escrow


@dataclass(slots=True, frozen=True)
class VaultAttestationInput:
    escrow_id: UUID
    operator_id: str
    nonce: str
    signature: str
    vault_ref: str
    raw_body: bytes


async def record_vault_attestation(
    session: AsyncSession,
    inp: VaultAttestationInput,
    *,
    correlation_id: UUID,
) -> Escrow:
    repo = EscrowRepository(session)
    escrow = await repo.find(inp.escrow_id)
    if escrow is None:
        raise NotFoundError(f"escrow {inp.escrow_id} not found")
    if escrow.state != EscrowState.FUNDS_LOCKED:
        raise WrongStateError(
            f"escrow {inp.escrow_id} not in FUNDS_LOCKED (state={escrow.state.value})"
        )
    attestation_id = uuid4()
    row = VaultAttestationRow(
        attestation_id=attestation_id,
        escrow_id=inp.escrow_id,
        vault_operator_id=inp.operator_id,
        payload_hash=_sha256_hex(inp.raw_body),
        nonce=inp.nonce,
        signature=inp.signature,
    )
    session.add(row)
    await session.flush()
    escrow.record_vault_attestation(attestation_id=attestation_id, payload_hash=row.payload_hash)
    await repo.upsert(escrow)
    await EventStore(session).append(
        stream_id=escrow.escrow_id,
        events=escrow.pull_events(),
        correlation_id=correlation_id,
    )
    return escrow


async def mint_certificate(
    session: AsyncSession,
    *,
    escrow_id: UUID,
    chain: ChainClient,
    ipfs_hash: str,
    correlation_id: UUID,
) -> Escrow:
    repo = EscrowRepository(session)
    escrow = await repo.find(escrow_id)
    if escrow is None:
        raise NotFoundError(f"escrow {escrow_id} not found")
    if escrow.state != EscrowState.VAULT_ATTESTED:
        raise WrongStateError(
            f"escrow {escrow_id} not in VAULT_ATTESTED (state={escrow.state.value})"
        )
    buyer = await session.get(UserRow, escrow.buyer_id)
    if buyer is None:
        raise NotFoundError(f"buyer {escrow.buyer_id} not found")

    mint = await chain.mint_certificate(
        owner_wallet=buyer.wallet_address or "0x0",
        ipfs_hash=ipfs_hash,
        idempotency_key=str(escrow_id),
    )

    certificate_id = uuid4()
    session.add(
        CertificateRow(
            certificate_id=certificate_id,
            asset_id=escrow.asset_id,
            owner_user_id=escrow.buyer_id,
            token_id=Decimal(mint.token_id),
            contract_address=mint.contract_address,
            tx_hash=mint.tx_hash,
            ipfs_metadata_hash=ipfs_hash,
            minted_at=datetime.now(UTC),
        )
    )
    await session.flush()

    escrow.record_certificate_mint(
        certificate_id=certificate_id,
        token_id=TokenId(mint.token_id),
        tx_hash=TxHash(mint.tx_hash),
        ipfs_hash=IpfsHash(ipfs_hash),
    )
    await repo.upsert(escrow)
    await EventStore(session).append(
        stream_id=escrow.escrow_id,
        events=escrow.pull_events(),
        correlation_id=correlation_id,
    )
    return escrow


async def release_escrow(session: AsyncSession, *, escrow_id: UUID, correlation_id: UUID) -> Escrow:
    escrow_repo = EscrowRepository(session)
    user_repo = UserRepository(session)
    escrow = await escrow_repo.find(escrow_id)
    if escrow is None:
        raise NotFoundError(f"escrow {escrow_id} not found")
    if escrow.state != EscrowState.CERTIFICATE_MINTED:
        raise WrongStateError(
            f"escrow {escrow_id} not in CERTIFICATE_MINTED (state={escrow.state.value})"
        )
    buyer = await user_repo.find(escrow.buyer_id)
    seller = await user_repo.find(escrow.seller_id)
    if buyer is None or seller is None:
        raise NotFoundError("buyer or seller not found")

    buyer.release_locked(escrow.amount)
    seller.credit(escrow.amount)
    escrow.release()

    await user_repo.upsert(buyer)
    await user_repo.upsert(seller)
    await escrow_repo.upsert(escrow)
    event_store = EventStore(session)
    for streamed_user in (buyer, seller):
        await event_store.append(
            stream_id=streamed_user.user_id,
            events=streamed_user.pull_events(),
            correlation_id=correlation_id,
        )
    await event_store.append(
        stream_id=escrow.escrow_id,
        events=escrow.pull_events(),
        correlation_id=correlation_id,
    )
    return escrow


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
