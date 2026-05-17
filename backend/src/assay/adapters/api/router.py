from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request, status

from assay.adapters.persistence import EscrowRepository, EventStore, UserRepository
from assay.application import use_cases as uc
from assay.domain import Money, TxHash, User

from .dependencies import (
    AdminUserId,
    ChainDep,
    HmacDep,
    JwtDep,
    SessionDep,
)
from .schemas import (
    AssetResponse,
    AuthTokenResponse,
    DepositRequest,
    EscrowResponse,
    KycDecisionRequest,
    LoginRequest,
    MintCertificateRequest,
    OpenEscrowRequest,
    RegisterAssetRequest,
    RegisterUserRequest,
    UserResponse,
    VaultAttestationRequest,
)

api_router = APIRouter(prefix="/api/v1")


@api_router.post("/auth/login", response_model=AuthTokenResponse, tags=["auth"])
async def login(body: LoginRequest, session: SessionDep, jwt: JwtDep) -> AuthTokenResponse:
    result = await uc.authenticate(session, email=body.email, password=body.password)
    token = jwt.issue(user_id=result.user_id, is_admin=result.is_admin)
    return AuthTokenResponse(
        access_token=token.access_token, token_type=token.token_type, expires_in=token.expires_in
    )


@api_router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
async def register_user(body: RegisterUserRequest, session: SessionDep) -> UserResponse:
    user = await uc.register_user(
        session,
        uc.RegisterUserInput(
            email=str(body.email),
            password=body.password,
            wallet_address=body.wallet_address,
        ),
        correlation_id=uuid4(),
    )
    return _user_response(user)


@api_router.post(
    "/users/{user_id}/kyc",
    response_model=UserResponse,
    tags=["users"],
)
async def kyc_decision(
    user_id: UUID,
    body: KycDecisionRequest,
    session: SessionDep,
    _admin: AdminUserId,
) -> UserResponse:
    if body.decision == "APPROVED":
        approved = await uc.approve_kyc(session, user_id=user_id, correlation_id=uuid4())
        return _user_response(approved)
    repo = UserRepository(session)
    rejected = await repo.find(user_id)
    if rejected is None:
        raise uc.NotFoundError(f"user {user_id} not found")
    rejected.reject_kyc(body.reason or "rejected by admin")
    await repo.upsert(rejected)
    await EventStore(session).append(
        stream_id=rejected.user_id, events=rejected.pull_events(), correlation_id=uuid4()
    )
    return _user_response(rejected)


@api_router.post(
    "/users/{user_id}/deposit",
    response_model=UserResponse,
    tags=["users"],
)
async def deposit(
    user_id: UUID,
    body: DepositRequest,
    session: SessionDep,
    _admin: AdminUserId,
) -> UserResponse:
    user = await uc.deposit_funds(
        session,
        user_id=user_id,
        amount=Money.from_str(body.amount_usdc),
        tx_hash=TxHash(body.tx_hash),
        correlation_id=uuid4(),
    )
    return _user_response(user)


@api_router.post(
    "/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["assets"],
)
async def register_asset(
    body: RegisterAssetRequest, session: SessionDep, _admin: AdminUserId
) -> AssetResponse:
    asset = await uc.register_asset(
        session,
        uc.RegisterAssetInput(
            asset_type=body.asset_type,
            lab_cert_number=body.lab_cert_number,
            vault_location=body.vault_location,
            owner_user_id=body.owner_user_id,
            grade=body.grade,
            weight_troy_oz=body.weight_troy_oz,
            photo_ipfs_hash=body.photo_ipfs_hash,
        ),
        correlation_id=uuid4(),
    )
    return AssetResponse(
        asset_id=asset.asset_id,
        asset_type=asset.asset_type,
        grade=asset.grade,
        weight_troy_oz=asset.weight_troy_oz,
        lab_cert_number=asset.lab_cert_number,
        vault_location=asset.vault_location,
        owner_user_id=asset.owner_user_id,
        photo_ipfs_hash=asset.photo_ipfs_hash.value if asset.photo_ipfs_hash else None,
    )


@api_router.post(
    "/escrows",
    response_model=EscrowResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["escrows"],
)
async def open_escrow(
    body: OpenEscrowRequest, session: SessionDep, _admin: AdminUserId
) -> EscrowResponse:
    escrow = await uc.open_escrow(
        session,
        uc.OpenEscrowInput(
            buyer_id=body.buyer_id,
            seller_id=body.seller_id,
            asset_id=body.asset_id,
            amount=Money.from_str(body.amount_usdc),
        ),
        correlation_id=uuid4(),
    )
    return await _read_escrow(session, escrow.escrow_id)


@api_router.post("/escrows/{escrow_id}/lock-funds", response_model=EscrowResponse, tags=["escrows"])
async def lock_funds(escrow_id: UUID, session: SessionDep, _user: AdminUserId) -> EscrowResponse:
    await uc.lock_funds(session, escrow_id=escrow_id, correlation_id=uuid4())
    return await _read_escrow(session, escrow_id)


@api_router.post("/escrows/{escrow_id}/mint", response_model=EscrowResponse, tags=["escrows"])
async def mint_certificate(
    escrow_id: UUID,
    body: MintCertificateRequest,
    session: SessionDep,
    chain: ChainDep,
    _admin: AdminUserId,
) -> EscrowResponse:
    await uc.mint_certificate(
        session,
        escrow_id=escrow_id,
        chain=chain,
        ipfs_hash=body.ipfs_metadata_hash,
        correlation_id=uuid4(),
    )
    return await _read_escrow(session, escrow_id)


@api_router.post("/escrows/{escrow_id}/release", response_model=EscrowResponse, tags=["escrows"])
async def release_escrow(
    escrow_id: UUID, session: SessionDep, _admin: AdminUserId
) -> EscrowResponse:
    await uc.release_escrow(session, escrow_id=escrow_id, correlation_id=uuid4())
    return await _read_escrow(session, escrow_id)


@api_router.get("/escrows/{escrow_id}", response_model=EscrowResponse, tags=["escrows"])
async def get_escrow(escrow_id: UUID, session: SessionDep) -> EscrowResponse:
    return await _read_escrow(session, escrow_id)


@api_router.post(
    "/vault/attest",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["vault"],
)
async def vault_attest(  # noqa: PLR0913 — webhook payload + 3 required headers + DI
    request: Request,
    body: VaultAttestationRequest,
    session: SessionDep,
    verifier: HmacDep,
    operator_id: Annotated[str, Header(alias="X-Assay-Operator-Id")],
    nonce: Annotated[str, Header(alias="X-Assay-Nonce")],
    signature: Annotated[str, Header(alias="X-Assay-Signature")],
) -> dict[str, str]:
    raw = await request.body()
    verifier.verify(operator_id=operator_id, body=raw, signature_b64=signature)
    await uc.record_vault_attestation(
        session,
        uc.VaultAttestationInput(
            escrow_id=body.escrow_id,
            operator_id=operator_id,
            nonce=nonce,
            signature=signature,
            vault_ref=body.vault_ref,
            raw_body=raw,
        ),
        correlation_id=uuid4(),
    )
    return {"status": "accepted"}


@api_router.get("/audit/export", tags=["audit"])
async def audit_export(
    session: SessionDep,
    _admin: AdminUserId,
    frm: Annotated[datetime, Query(alias="from")],
    to: Annotated[datetime, Query()],
) -> dict[str, object]:
    events = await EventStore(session).export_window(frm=frm, to=to)
    return {
        "from": frm.isoformat(),
        "to": to.isoformat(),
        "count": len(events),
        "events": [
            {
                "event_id": str(e.event_id),
                "stream_id": str(e.stream_id),
                "stream_type": e.stream_type,
                "version": e.version,
                "event_type": e.event_type,
                "payload": e.payload,
                "correlation_id": str(e.correlation_id),
                "ts": e.ts.isoformat(),
            }
            for e in events
        ],
    }


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        email=user.email.value,
        kyc_status=user.kyc_status.value,
        wallet_address=user.wallet_address,
        available_balance=str(user.available_balance),
        locked_balance=str(user.locked_balance),
    )


async def _read_escrow(session: SessionDep, escrow_id: UUID) -> EscrowResponse:
    repo = EscrowRepository(session)
    view = await repo.read(escrow_id)
    if view is None:
        raise uc.NotFoundError(f"escrow {escrow_id} not found")
    return EscrowResponse(
        escrow_id=view.escrow_id,
        buyer_id=view.buyer_id,
        seller_id=view.seller_id,
        asset_id=view.asset_id,
        amount_usdc=view.amount_usdc,
        state=view.state,
        opened_at=view.opened_at,
        locked_at=view.locked_at,
        attested_at=view.attested_at,
        minted_at=view.minted_at,
        released_at=view.released_at,
    )
