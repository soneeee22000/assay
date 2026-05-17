from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from assay.domain import (
    Asset,
    EmailAddress,
    Escrow,
    IpfsHash,
    Money,
    TokenId,
    TxHash,
    User,
)


@pytest.fixture
def usdc_100() -> Money:
    return Money(Decimal("100.000000"))


@pytest.fixture
def usdc_50() -> Money:
    return Money(Decimal("50.000000"))


@pytest.fixture
def usdc_1() -> Money:
    return Money(Decimal("1.000000"))


@pytest.fixture
def buyer_id() -> UUID:
    return uuid4()


@pytest.fixture
def seller_id() -> UUID:
    return uuid4()


@pytest.fixture
def asset_id() -> UUID:
    return uuid4()


@pytest.fixture
def kyc_approved_user() -> User:
    user = User.register(
        user_id=uuid4(),
        email=EmailAddress("alice@example.com"),
    )
    user.approve_kyc()
    user.pull_events()
    return user


@pytest.fixture
def pending_escrow(buyer_id: UUID, seller_id: UUID, asset_id: UUID, usdc_100: Money) -> Escrow:
    escrow = Escrow.open(
        escrow_id=uuid4(),
        buyer_id=buyer_id,
        seller_id=seller_id,
        asset_id=asset_id,
        amount=usdc_100,
    )
    escrow.pull_events()
    return escrow


@pytest.fixture
def funds_locked_escrow(pending_escrow: Escrow) -> Escrow:
    pending_escrow.lock_funds()
    pending_escrow.pull_events()
    return pending_escrow


@pytest.fixture
def vault_attested_escrow(funds_locked_escrow: Escrow) -> Escrow:
    funds_locked_escrow.record_vault_attestation(
        attestation_id=uuid4(),
        payload_hash="hash-deadbeef",
    )
    funds_locked_escrow.pull_events()
    return funds_locked_escrow


@pytest.fixture
def minted_escrow(vault_attested_escrow: Escrow) -> Escrow:
    vault_attested_escrow.record_certificate_mint(
        certificate_id=uuid4(),
        token_id=TokenId(1),
        tx_hash=TxHash("0x" + "ab" * 32),
        ipfs_hash=IpfsHash("QmTestHashForCertificateMetadata"),
    )
    vault_attested_escrow.pull_events()
    return vault_attested_escrow


@pytest.fixture
def sample_asset(seller_id: UUID, asset_id: UUID) -> Asset:
    return Asset.register(
        asset_id=asset_id,
        asset_type="gold-bar",
        lab_cert_number="LBMA-2026-001",
        vault_location="ZUR-VAULT-A",
        owner_user_id=seller_id,
        grade="999.9",
        weight_troy_oz=Decimal("400.000"),
        photo_ipfs_hash=IpfsHash("QmAssetPhotoSampleHashAaa"),
    )
