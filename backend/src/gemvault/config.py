from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config loaded from environment / .env. See `.env.example`."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", frozen=True
    )

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://gemvault:gemvault@localhost:5432/gemvault"

    jwt_secret: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_expires_seconds: int = 3600

    base_rpc_url: str = "https://sepolia.base.org"
    base_chain_id: int = 84532
    certificate_contract_address: str = "0x0000000000000000000000000000000000000000"
    admin_private_key: str = ""
    usdc_contract_address: str = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

    pinata_jwt: str = ""
    ipfs_gateway_url: str = "https://gateway.pinata.cloud/ipfs"

    vault_hmac_secrets: str = ""
    """Comma-separated `operator_id:secret` pairs."""

    basescan_api_key: str = ""

    cors_origins: str = ""
    """Comma-separated extra allowed CORS origins (e.g. the live frontend URL)."""

    def allowed_origins(self) -> list[str]:
        defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
        extra = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return [*defaults, *extra]

    def vault_secrets(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for pair in filter(None, (p.strip() for p in self.vault_hmac_secrets.split(","))):
            operator, _, secret = pair.partition(":")
            if operator and secret:
                out[operator] = secret
        return out
