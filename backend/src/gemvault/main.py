from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gemvault import __version__
from gemvault.adapters.api import api_router, install_exception_handlers
from gemvault.adapters.api.dependencies import settings

_DESCRIPTION = (
    "Reference RWA fintech backend: financial-grade ledger + on-chain certificate orchestration."
)

app = FastAPI(
    title="GemVault Backend",
    version=__version__,
    description=_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().allowed_origins(),
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
