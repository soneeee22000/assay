from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gemvault import __version__
from gemvault.adapters.api import api_router, install_exception_handlers

_DESCRIPTION = (
    "Reference RWA fintech backend: financial-grade ledger + on-chain certificate orchestration."
)


def _cors_origins() -> list[str]:
    """Allowed CORS origins: localhost defaults plus any comma-separated
    entries in CORS_ORIGINS. Read from the environment directly so importing
    this module never requires the full runtime Settings."""
    defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
    extra = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
    return [*defaults, *extra]

app = FastAPI(
    title="GemVault Backend",
    version=__version__,
    description=_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-Id"],
)

install_exception_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["meta"])
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": __version__})
