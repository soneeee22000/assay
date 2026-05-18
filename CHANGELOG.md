# Changelog

All notable changes to Assay are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Project repositioned: GemVault → Assay.** Renamed end-to-end — Python package `gemvault` → `assay`, smart contract `GemVaultCertificate` → `AssayCertificate` (ERC-721 symbol `GVC` → `ASC`), the GitHub repository, environment variables, and the HMAC webhook headers (`X-GemVault-*` → `X-Assay-*`). Re-themed from gemstone RWA tokenisation to vaulted precious-metals / allocated-bullion custody: the `Asset` domain now models gold and silver bars, the weight field is `weight_troy_oz` (was `weight_carats`), and `lab_cert_number` carries an LBMA-accredited assayer reference. The escrow lifecycle, event-sourced ledger, and certificate mechanics are unchanged — the rename is copy and identifiers.
- Live deployment re-provisioned under the new name: dashboard on Vercel (<https://assay-nine.vercel.app>), API + managed Postgres on Railway (<https://assay-api-production.up.railway.app>), and `AssayCertificate` redeployed and source-verified on Base Sepolia at `0xdC409dBC3eb2824F2a7c7a1D0Cec2aeD34dAAe30`. The live backend is pre-seeded with a full escrow lifecycle.
- Landing page rewritten as a narrative — hook, the problem with paper-based ownership, how Assay closes the gap, the end-to-end escrow lifecycle, and proof — instead of a dry technical hero. README gains a "Why Assay exists" section framing the same problem.
- Landing page restyled into a premium dark theme — a deep-ink palette, a technical hairline grid, and a gold signature accent (the precious-metal brand), scoped via a `.theme-landing` class so the dashboard's adaptive theme is untouched. A new Assay brand mark (a gold monoline "A") replaces the legacy gemstone icon, and `app/icon.svg` adds a proper favicon.

### Added

- `BaseChainClient` — a real `web3.py` implementation of the `ChainClient` port that signs and broadcasts `mint` / `attestVault` transactions to Base Sepolia and waits for the receipt. Selection is key-gated in `dependencies._chain()`: with an `ADMIN_PRIVATE_KEY` configured the backend uses the real client, otherwise it falls back to `StubChainClient`, so CI and local dev stay hermetic. On-chain token ids are derived deterministically from the escrow id. New `scripts/verify_chain.py` does a one-off real mint to verify the client end-to-end. See ADR-005.
- `.github/workflows/verify-contract.yml` — manual-dispatch contract source verification, so an already-deployed address can be verified without a redeploy.
- Env-driven CORS — a `CORS_ORIGINS` variable lets the live frontend origin be set at deploy time instead of being hardcoded in `main.py`.
- `frontend/e2e/record.spec.ts` + `frontend/playwright.config.ts` — Playwright walk-through that records the demo GIF against the live deploy.
- Premium UX pass on the admin dashboard — Fira Sans / Fira Code typography via `next/font/google`, Lucide-React iconography throughout, blue-centric primary with amber accent oklch tokens, KPI cards on every page, full dark-mode token set, uniform 2px focus ring, `prefers-reduced-motion` support. New primitive layer in `frontend/src/components/ui.tsx` (Button · Badge · Card · KpiCard · EmptyState · Spinner · LoadingRow · ErrorRow · BrandMark).
- `GETTING-STARTED.md` — step-by-step local runbook with troubleshooting table.
- Annotated `backend/.env.example` linking each production-only signup (Alchemy · Coinbase Developer Platform · Basescan · Pinata · Railway · Vercel) to its purpose.
- Sprint 6 deploy scaffolding: `backend/railway.toml`, `frontend/vercel.json`, `.github/workflows/deploy-contract.yml` (manual-dispatch Foundry deploy on Base Sepolia with secrets), `scripts/demo/seed.py` (drives a full escrow lifecycle), `frontend/e2e/record.spec.ts` (Playwright demo recording).
- `docs/DEPLOY.md` — end-to-end Railway + Vercel + Foundry deploy recipe with cost estimate.

### Fixed

- Etherscan retired its V1 API; `contracts/foundry.toml` now lets Foundry resolve the Etherscan V2 endpoint, so `forge` contract source verification succeeds.
- `backend/Dockerfile` copies `README.md` into the image — Hatchling needs it for package metadata, so the Railway build no longer fails at `pip install -e .`.
- `backend/railway.toml` — healthcheck window widened to 300s for a cold Python container, and the start command wrapped in `sh -c` so Railway expands `$PORT`.
- `assay.main` no longer instantiates `Settings` at import time, so importing the app never requires runtime secrets (unblocked CI test collection).
- `docker-compose` Postgres now binds `5433:5432` to side-step machines that already run a native PostgreSQL service on `:5432`.
- `alembic env.py` loads `backend/.env` on its own via a minimal stdlib parser so `alembic upgrade head` works without pre-exporting `DATABASE_URL`.
- `scripts/demo/seed.py` forces stdout to UTF-8 at startup; Windows `cp1252` consoles no longer crash on the script's `→` arrows.

## [0.1.0] — 2026-05-11

Initial scaffold of the RWA fintech reference architecture. Six sprints landed end-to-end.

### Sprint 5 — Next.js admin dashboard

- Four views wired to the FastAPI backend: `/login`, `/ledger`, `/escrows`, `/escrows/[id]`, `/certificates`.
- Stub JWT auth stored in localStorage; AuthGate redirects to `/login` when no token is present.
- CORS middleware on the backend so the dashboard and a future Vercel deploy can reach the API.
- Mobile-first responsive layouts; oklch design tokens in `globals.css`; no shadcn registry, no emoji-as-icons.

### Sprint 4 — FastAPI HTTP layer

- 11-endpoint REST surface across `auth`, `users`, `assets`, `escrows`, `vault`, `audit`.
- scrypt password hashing + python-jose JWT (stub auth per ADR-004).
- HMAC-SHA256 vault webhook with `(operator_id, nonce)` replay protection.
- RFC 7807 problem-details errors, idempotency-key support, signed audit-trail export.
- Full E2E happy-path test that drives `register → kyc → deposit → asset → escrow → lock → attest → mint → release → audit-export`.

### Sprint 3 — Smart contract

- `AssayCertificate.sol` — ERC-721 with vault-attestation transfer gate (`_update` override), `Pausable`, `AccessControl` (`MINTER_ROLE`, `ATTESTER_ROLE`, `PAUSER_ROLE`).
- Foundry unit + invariant tests; `forge script Deploy --broadcast --verify` ready for Base Sepolia.

### Sprint 2 — Persistence

- SQLAlchemy 2 async models for `users`, `assets`, `escrows`, `certificates`, `vault_attestations`, `events`, `ledger_entries`.
- Append-only event store (single-table per ADR-003) with optimistic concurrency on `(stream_id, version)`.
- Projection repositories for User and Escrow with aggregate rehydration.
- Alembic migration `0001_initial.py`.
- Integration tests via testcontainers; skip cleanly when Docker is unavailable.

### Sprint 1 — Domain layer

- Pure-Python domain layer: 5 entities (`User`, `Asset`, `Escrow`, `Certificate`, `VaultAttestation`), 6 value objects (`Money`, `EmailAddress`, `IpfsHash`, `TokenId`, `HmacNonce`, `TxHash`), 13 domain events.
- Seven-state escrow machine: `PENDING → FUNDS_LOCKED → VAULT_ATTESTED → CERTIFICATE_MINTED → RELEASED` with `CANCELLED` / `REFUNDED` branches.
- 91 unit tests at 99% line coverage; zero framework imports inside `src/assay/domain/`.

### Sprint 0 — Scaffold

- Monorepo with `backend/`, `contracts/`, `frontend/`, `docs/`, `scripts/`.
- Dockerfile, `docker-compose.yml`, `.env.example`, `.gitignore` with confidential-file patterns.
- GitHub Actions CI matrix across Python (ruff + ruff format + mypy + pytest), Foundry (forge build + test + fmt), and Node (tsc + next build).

### CI fixes during initial bring-up

- Split backend pytest into a blocking unit-and-smoke step and a tolerated integration step; the latter hangs on the Linux runner under pytest-asyncio + testcontainers and is run with `continue-on-error: true` plus a 5-minute timeout.
- Dropped deprecated `forge install --no-commit` flag.
- Bumped Next.js from 15.1.0 to 16.2.6 to clear shipped security advisories; committed `package-lock.json`; dropped the removed `next lint` script.
- Expanded single-line `revert` statements in Solidity to satisfy `forge fmt --check`; flipped `bracket_spacing` to `false` in `foundry.toml`.

[Unreleased]: https://github.com/soneeee22000/assay/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/soneeee22000/assay/releases/tag/v0.1.0
