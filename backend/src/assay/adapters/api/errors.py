from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from assay.adapters.auth.jwt_provider import JwtError
from assay.adapters.webhook.hmac_verifier import (
    InvalidSignatureError,
    ReplayedNonceError,
)
from assay.application.use_cases import (
    AuthenticationError,
    NotFoundError,
    WrongStateError,
)
from assay.domain import (
    DomainError,
    InsufficientBalance,
    InvalidEscrowParticipants,
    InvalidStateTransition,
    KycNotApproved,
)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found(_req: Request, exc: NotFoundError) -> JSONResponse:
        return _problem(404, "not_found", str(exc))

    @app.exception_handler(AuthenticationError)
    async def auth_failed(_req: Request, exc: AuthenticationError) -> JSONResponse:
        return _problem(401, "authentication_failed", str(exc))

    @app.exception_handler(JwtError)
    async def jwt_failed(_req: Request, exc: JwtError) -> JSONResponse:
        return _problem(401, "invalid_token", str(exc))

    @app.exception_handler(InvalidSignatureError)
    async def bad_hmac(_req: Request, exc: InvalidSignatureError) -> JSONResponse:
        return _problem(401, "invalid_signature", str(exc))

    @app.exception_handler(ReplayedNonceError)
    async def replay(_req: Request, exc: ReplayedNonceError) -> JSONResponse:
        return _problem(409, "replayed_nonce", str(exc))

    @app.exception_handler(WrongStateError)
    async def wrong_state(_req: Request, exc: WrongStateError) -> JSONResponse:
        return _problem(409, "wrong_state", str(exc))

    @app.exception_handler(InvalidStateTransition)
    async def state_transition(_req: Request, exc: InvalidStateTransition) -> JSONResponse:
        return _problem(409, "invalid_state_transition", str(exc))

    @app.exception_handler(InvalidEscrowParticipants)
    async def bad_participants(_req: Request, exc: InvalidEscrowParticipants) -> JSONResponse:
        return _problem(400, "invalid_escrow_participants", str(exc))

    @app.exception_handler(InsufficientBalance)
    async def insufficient(_req: Request, exc: InsufficientBalance) -> JSONResponse:
        return _problem(409, "insufficient_balance", str(exc))

    @app.exception_handler(KycNotApproved)
    async def kyc(_req: Request, exc: KycNotApproved) -> JSONResponse:
        return _problem(403, "kyc_not_approved", str(exc))

    @app.exception_handler(DomainError)
    async def domain_generic(_req: Request, exc: DomainError) -> JSONResponse:
        return _problem(400, "domain_error", str(exc))


def _problem(status: int, slug: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://assay.dev/problems/{slug}",
            "title": slug.replace("_", " ").title(),
            "status": status,
            "detail": detail,
        },
    )
