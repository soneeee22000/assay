# Changelog

All notable changes to GemVault are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Premium UX pass on the admin dashboard — Fira Sans / Fira Code typography via `next/font/google`, Lucide-React iconography throughout, blue-centric primary with amber accent oklch tokens, KPI cards on every page, full dark-mode token set, uniform 2px focus ring, `prefers-reduced-motion` support. New primitive layer in `frontend/src/components/ui.tsx` (Button · Badge · Card · KpiCard · EmptyState · Spinner · LoadingRow · ErrorRow · BrandMark).
- `GETTING-STARTED.md` — step-by-step local runbook with troubleshooting table.
- Annotated `backend/.env.example` linking each production-only signup (Alchemy · Coinbase Developer Platform · Basescan · Pinata · Railway · Vercel) to its purpose.
- Sprint 6 deploy scaffolding: `backend/railway.toml`, `frontend/vercel.json`, `.github/workflows/deploy-contract.yml` (manual-dispatch Foundry deploy on Base Sepolia with secrets), `scripts/demo/seed.py` (drives a full escrow lifecycle), `scripts/demo/record.spec.ts` (Playwright demo recording).
- `docs/DEPLOY.md` — end-to-end Railway + Vercel + Foundry deploy recipe with cost estimate.

### Fixed

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

- `GemVaultCertificate.sol` — ERC-721 with vault-attestation transfer gate (`_update` override), `Pausable`, `AccessControl` (`MINTER_ROLE`, `ATTESTER_ROLE`, `PAUSER_ROLE`).
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
- 91 unit tests at 99% line coverage; zero framework imports inside `src/gemvault/domain/`.

### Sprint 0 — Scaffold

- Monorepo with `backend/`, `contracts/`, `frontend/`, `docs/`, `scripts/`.
- Dockerfile, `docker-compose.yml`, `.env.example`, `.gitignore` with confidential-file patterns.
- GitHub Actions CI matrix across Python (ruff + ruff format + mypy + pytest), Foundry (forge build + test + fmt), and Node (tsc + next build).

### CI fixes during initial bring-up

- Split backend pytest into a blocking unit-and-smoke step and a tolerated integration step; the latter hangs on the Linux runner under pytest-asyncio + testcontainers and is run with `continue-on-error: true` plus a 5-minute timeout.
- Dropped deprecated `forge install --no-commit` flag.
- Bumped Next.js from 15.1.0 to 16.2.6 to clear shipped security advisories; committed `package-lock.json`; dropped the removed `next lint` script.
- Expanded single-line `revert` statements in Solidity to satisfy `forge fmt --check`; flipped `bracket_spacing` to `false` in `foundry.toml`.

[Unreleased]: https://github.com/soneeee22000/gemvault/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/soneeee22000/gemvault/releases/tag/v0.1.0
