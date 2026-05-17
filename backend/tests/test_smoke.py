from __future__ import annotations

from fastapi.testclient import TestClient

from assay.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_health_response_contains_semver_version() -> None:
    client = TestClient(app)
    response = client.get("/health")

    version = response.json()["version"]
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
