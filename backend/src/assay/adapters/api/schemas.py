from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 — OAuth2 token_type
    expires_in: int


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    wallet_address: str | None = Field(default=None, min_length=42, max_length=42)


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    kyc_status: str
    wallet_address: str | None
    available_balance: str
    locked_balance: str


class KycDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED)$")
    reason: str | None = None


class DepositRequest(BaseModel):
    amount_usdc: str = Field(description="Decimal string, USDC, 6dp")
    tx_hash: str = Field(min_length=66, max_length=66)


class RegisterAssetRequest(BaseModel):
    asset_type: str = Field(min_length=1, max_length=64)
    lab_cert_number: str = Field(min_length=1, max_length=128)
    vault_location: str = Field(min_length=1, max_length=64)
    owner_user_id: UUID
    grade: str | None = None
    weight_troy_oz: Decimal | None = Field(default=None, gt=0)
    photo_ipfs_hash: str | None = None


class AssetResponse(BaseModel):
    asset_id: UUID
    asset_type: str
    grade: str | None
    weight_troy_oz: Decimal | None
    lab_cert_number: str
    vault_location: str
    owner_user_id: UUID
    photo_ipfs_hash: str | None


class OpenEscrowRequest(BaseModel):
    buyer_id: UUID
    seller_id: UUID
    asset_id: UUID
    amount_usdc: str


class EscrowResponse(BaseModel):
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


class MintCertificateRequest(BaseModel):
    ipfs_metadata_hash: str = Field(min_length=4, max_length=128)


class VaultAttestationRequest(BaseModel):
    escrow_id: UUID
    vault_ref: str = Field(min_length=1, max_length=64)
    attested_at: datetime
    attestation_result: str = Field(pattern="^(CONFIRMED|REJECTED)$")
    notes: str | None = None
