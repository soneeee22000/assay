from __future__ import annotations

import hashlib
import hmac
import json
from base64 import b64encode
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine

from assay.adapters.persistence import get_sessionmaker
from assay.adapters.persistence.models import UserRow

pytestmark = pytest.mark.asyncio


async def test_health_returns_ok(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_full_happy_path(client: AsyncClient, engine: AsyncEngine) -> None:
    admin = await client.post(
        "/api/v1/users",
        json={"email": "admin@example.com", "password": "adminpass1234"},
    )
    assert admin.status_code == 201, admin.text

    seller = await client.post(
        "/api/v1/users",
        json={"email": "seller@example.com", "password": "sellerpass1234"},
    )
    assert seller.status_code == 201
    seller_id = seller.json()["user_id"]

    buyer = await client.post(
        "/api/v1/users",
        json={"email": "buyer@example.com", "password": "buyerpass1234"},
    )
    assert buyer.status_code == 201
    buyer_id = buyer.json()["user_id"]

    await _bootstrap_admin(engine, email="admin@example.com")

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1234"},
    )
    assert login.status_code == 200
    admin_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    for uid in (seller_id, buyer_id):
        r = await client.post(
            f"/api/v1/users/{uid}/kyc",
            json={"decision": "APPROVED"},
            headers=headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["kyc_status"] == "APPROVED"

    deposit = await client.post(
        f"/api/v1/users/{buyer_id}/deposit",
        json={"amount_usdc": "500.0", "tx_hash": "0x" + "ab" * 32},
        headers=headers,
    )
    assert deposit.status_code == 200, deposit.text
    assert deposit.json()["available_balance"] == "500.000000"

    asset = await client.post(
        "/api/v1/assets",
        json={
            "asset_type": "gold-bar",
            "lab_cert_number": "LBMA-2026-001",
            "vault_location": "ZUR-A",
            "owner_user_id": seller_id,
            "grade": "999.9",
            "weight_troy_oz": "400.0",
            "photo_ipfs_hash": "QmAssetSampleHash",
        },
        headers=headers,
    )
    assert asset.status_code == 201, asset.text
    asset_id = asset.json()["asset_id"]

    escrow = await client.post(
        "/api/v1/escrows",
        json={
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "asset_id": asset_id,
            "amount_usdc": "100.0",
        },
        headers=headers,
    )
    assert escrow.status_code == 201, escrow.text
    escrow_id = escrow.json()["escrow_id"]
    assert escrow.json()["state"] == "PENDING"

    locked = await client.post(f"/api/v1/escrows/{escrow_id}/lock-funds", headers=headers)
    assert locked.status_code == 200, locked.text
    assert locked.json()["state"] == "FUNDS_LOCKED"

    attested = await _post_vault_attestation(client, escrow_id=escrow_id)
    assert attested.status_code == 202, attested.text

    get_after_attest = await client.get(f"/api/v1/escrows/{escrow_id}", headers=headers)
    assert get_after_attest.json()["state"] == "VAULT_ATTESTED"

    minted = await client.post(
        f"/api/v1/escrows/{escrow_id}/mint",
        json={"ipfs_metadata_hash": "QmCertMetadataSampleHash"},
        headers=headers,
    )
    assert minted.status_code == 200, minted.text
    assert minted.json()["state"] == "CERTIFICATE_MINTED"

    released = await client.post(f"/api/v1/escrows/{escrow_id}/release", headers=headers)
    assert released.status_code == 200, released.text
    assert released.json()["state"] == "RELEASED"

    now = datetime.now(UTC)
    audit = await client.get(
        "/api/v1/audit/export",
        params={
            "from": (now - timedelta(hours=1)).isoformat(),
            "to": (now + timedelta(hours=1)).isoformat(),
        },
        headers=headers,
    )
    assert audit.status_code == 200, audit.text
    payload = audit.json()
    event_types = {e["event_type"] for e in payload["events"]}
    assert {
        "UserRegistered",
        "KycApproved",
        "FundsDeposited",
        "AssetRegistered",
        "EscrowOpened",
        "FundsLocked",
        "VaultAttested",
        "CertificateMinted",
        "EscrowReleased",
    } <= event_types


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "victim@example.com", "password": "rightpassword1"},
    )
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "wrongpassword2"},
    )
    assert bad.status_code == 401


async def test_admin_endpoint_rejects_missing_bearer(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/assets",
        json={
            "asset_type": "silver-bar",
            "lab_cert_number": "LBMA-X",
            "vault_location": "PAR-A",
            "owner_user_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert r.status_code == 401


async def test_vault_attest_rejects_bad_signature(client: AsyncClient, engine: AsyncEngine) -> None:
    body = {
        "escrow_id": "00000000-0000-0000-0000-000000000099",
        "vault_ref": "ZUR-X-1",
        "attested_at": datetime.now(UTC).isoformat(),
        "attestation_result": "CONFIRMED",
    }
    r = await client.post(
        "/api/v1/vault/attest",
        content=json.dumps(body),
        headers={
            "X-Assay-Operator-Id": "vault-test",
            "X-Assay-Nonce": "test-nonce-aaaaaaaaaaaa",
            "X-Assay-Signature": "QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE=",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401, r.text


async def _bootstrap_admin(engine: AsyncEngine, *, email: str) -> None:
    sessions = get_sessionmaker(engine)
    async with sessions() as s:
        await s.execute(update(UserRow).where(UserRow.email == email).values(kyc_status="APPROVED"))
        await s.commit()


async def _post_vault_attestation(client: AsyncClient, *, escrow_id: str):
    body = {
        "escrow_id": escrow_id,
        "vault_ref": "ZUR-A-2026-05-11-01",
        "attested_at": datetime.now(UTC).isoformat(),
        "attestation_result": "CONFIRMED",
    }
    raw = json.dumps(body).encode("utf-8")
    mac = hmac.new(b"supersecret-vault-key", raw, hashlib.sha256).digest()
    sig = b64encode(mac).decode("ascii")
    return await client.post(
        "/api/v1/vault/attest",
        content=raw,
        headers={
            "X-Assay-Operator-Id": "vault-test",
            "X-Assay-Nonce": "happy-path-nonce-" + escrow_id[:8],
            "X-Assay-Signature": sig,
            "Content-Type": "application/json",
        },
    )
