"""Drive a full escrow lifecycle against a running backend so the dashboard has real data.

Usage (with the backend on :8000):

    python scripts/demo/seed.py

Optional env:
    ASSAY_API_BASE  default http://localhost:8000
    ASSAY_ADMIN_EMAIL / _PASSWORD  default admin@example.com / adminpass1234

The script is idempotent-friendly: it tolerates "already registered" responses
and continues. It exits 0 if at least one escrow reached the RELEASED state.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from base64 import b64encode
from datetime import UTC, datetime
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

# Windows consoles default to cp1252, which can't render the arrows used below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = os.environ.get("ASSAY_API_BASE", "http://localhost:8000")
ADMIN_EMAIL = os.environ.get("ASSAY_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ASSAY_ADMIN_PASSWORD", "adminpass1234")
VAULT_SECRET = os.environ.get("VAULT_HMAC_SECRET", "supersecret-vault-key")
VAULT_OPERATOR = os.environ.get("VAULT_OPERATOR_ID", "vault-test")
DB_URL = os.environ.get("DATABASE_URL_SYNC")


def register(client: httpx.Client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/users",
        json={"email": email, "password": password},
    )
    if response.status_code == 201:
        return response.json()["user_id"]
    # Fall back: log in to discover the user id via the JWT subject claim.
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    import base64

    payload = json.loads(
        base64.urlsafe_b64decode(token.split(".")[1] + "==").decode("utf-8")
    )
    return str(payload["sub"])


def promote_admin(email: str) -> None:
    """Approve the admin's KYC directly via SQL so the user can sign in as admin."""
    if not DB_URL:
        print(
            f"WARN: DATABASE_URL_SYNC not set; you'll need to approve {email} manually.",
            file=sys.stderr,
        )
        return
    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET kyc_status='APPROVED' WHERE email=%s",
                (email,),
            )
            conn.commit()


def login(client: httpx.Client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


def approve_kyc(client: httpx.Client, user_id: str, headers: dict[str, str]) -> None:
    response = client.post(
        f"/api/v1/users/{user_id}/kyc",
        json={"decision": "APPROVED"},
        headers=headers,
    )
    response.raise_for_status()


def deposit(
    client: httpx.Client,
    user_id: str,
    amount: str,
    headers: dict[str, str],
) -> None:
    response = client.post(
        f"/api/v1/users/{user_id}/deposit",
        json={"amount_usdc": amount, "tx_hash": "0x" + "ab" * 32},
        headers=headers,
    )
    response.raise_for_status()


def register_asset(
    client: httpx.Client,
    owner_id: str,
    headers: dict[str, str],
    lab_cert_number: str,
) -> str:
    response = client.post(
        "/api/v1/assets",
        json={
            "asset_type": "gold-bar",
            "lab_cert_number": lab_cert_number,
            "vault_location": "ZUR-VAULT-A",
            "owner_user_id": owner_id,
            "grade": "999.9",
            "weight_troy_oz": "400.000",
            "photo_ipfs_hash": "QmDemoGoldBarPhoto",
        },
        headers=headers,
    )
    response.raise_for_status()
    return str(response.json()["asset_id"])


def open_escrow(
    client: httpx.Client,
    buyer_id: str,
    seller_id: str,
    asset_id: str,
    amount: str,
    headers: dict[str, str],
) -> str:
    response = client.post(
        "/api/v1/escrows",
        json={
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "asset_id": asset_id,
            "amount_usdc": amount,
        },
        headers=headers,
    )
    response.raise_for_status()
    return str(response.json()["escrow_id"])


def post_step(
    client: httpx.Client, escrow_id: str, action: str, headers: dict[str, str]
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/escrows/{escrow_id}/{action}", headers=headers
    )
    response.raise_for_status()
    return dict(response.json())


def post_mint(
    client: httpx.Client, escrow_id: str, headers: dict[str, str]
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/escrows/{escrow_id}/mint",
        json={"ipfs_metadata_hash": "QmDemoCertMetadataHash"},
        headers=headers,
    )
    response.raise_for_status()
    return dict(response.json())


def vault_attest(client: httpx.Client, escrow_id: str) -> None:
    body = {
        "escrow_id": escrow_id,
        "vault_ref": f"ZUR-A-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
        "attested_at": datetime.now(UTC).isoformat(),
        "attestation_result": "CONFIRMED",
    }
    raw = json.dumps(body).encode("utf-8")
    mac = hmac.new(VAULT_SECRET.encode("utf-8"), raw, hashlib.sha256).digest()
    sig = b64encode(mac).decode("ascii")
    response = client.post(
        "/api/v1/vault/attest",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Assay-Operator-Id": VAULT_OPERATOR,
            "X-Assay-Nonce": f"seed-{escrow_id[:12]}-{datetime.now(UTC).timestamp()}",
            "X-Assay-Signature": sig,
        },
    )
    response.raise_for_status()


def main() -> int:
    with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
        print(f"→ Register admin {ADMIN_EMAIL}")
        register(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        promote_admin(ADMIN_EMAIL)

        print(f"→ Sign in as {ADMIN_EMAIL}")
        admin_token = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {admin_token}"}

        print("→ Register buyer + seller")
        buyer_id = register(client, "buyer@example.com", "buyerpass1234")
        seller_id = register(client, "seller@example.com", "sellerpass1234")

        print("→ Approve KYC for buyer + seller")
        approve_kyc(client, buyer_id, headers)
        approve_kyc(client, seller_id, headers)

        print("→ Fund the buyer with 500 USDC")
        deposit(client, buyer_id, "500.0", headers)

        print("→ Register a gold-bar asset to the seller")
        asset_id = register_asset(
            client,
            seller_id,
            headers,
            lab_cert_number=f"LBMA-DEMO-{datetime.now(UTC).strftime('%H%M%S')}",
        )

        print("→ Open an escrow for 100 USDC")
        escrow_id = open_escrow(client, buyer_id, seller_id, asset_id, "100.0", headers)

        print("→ Lock funds")
        post_step(client, escrow_id, "lock-funds", headers)

        print("→ Vault attestation (HMAC-signed webhook)")
        vault_attest(client, escrow_id)

        print("→ Mint certificate")
        post_mint(client, escrow_id, headers)

        print("→ Release escrow")
        result = post_step(client, escrow_id, "release", headers)

        assert result["state"] == "RELEASED", f"unexpected final state {result['state']}"
        print(f"✓ Escrow {escrow_id} reached RELEASED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
