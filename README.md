# GemVault — RWA Fintech Reference Architecture

[![CI](https://github.com/soneeee22000/gemvault/actions/workflows/ci.yml/badge.svg)](https://github.com/soneeee22000/gemvault/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688)](https://fastapi.tiangolo.com/)
[![Solidity](https://img.shields.io/badge/solidity-0.8.28-363636)](https://soliditylang.org/)
[![Next.js](https://img.shields.io/badge/next.js-16-black)](https://nextjs.org/)

Physical high-value collectibles tokenised as ERC-721 certificates of authenticity, settled through a custodian-backed escrow lifecycle, on a financial-grade event-sourced ledger. Built end-to-end across Solidity, Python, and TypeScript — one repo, one demo, all the layers a fintech-meets-RWA platform actually needs to ship.

> **Live demo:** _add the Vercel + Railway URLs after first deploy — see [`docs/DEPLOY.md`](./docs/DEPLOY.md)_

---

## Why this exists

Most Web3 portfolios prove one skill: "I can write a Solidity contract" OR "I can integrate a wallet" OR "I can ship a dashboard." This one proves the layer fintech-meets-RWA companies actually need — a clean, regulated-grade backend that owns the ledger, the audit log, the escrow lifecycle, AND the on-chain certification layer, in one vertical slice.

The wedge: telecom event-pipeline experience (CDR / SMPP, Kafka) and healthcare compliance work (VitaLens, ComplyOS — EU AI Act) port directly into financial event sourcing and regulated audit trails. Rare combination on an RWA fintech application stack.

---

## The five-minute reviewer path

1. **Open the live dashboard** — sign in, click through Ledger → Escrows → Certificates.
2. **Open `docs/ARCHITECTURE.md`** — system context + hexagonal diagram + escrow state machine + Postgres schema, all in one place.
3. **Open `docs/adr/decisions.md`** — four locked architecture decisions with alternatives considered (ADR-001 ERC-721 vs ERC-3525, ADR-002 vault attestation model, ADR-003 single events table, ADR-004 stub auth).
4. **Open `docs/openapi.yaml`** — the 14-endpoint API surface, RFC 7807 errors, idempotency-key support.
5. **Open `.github/workflows/ci.yml`** — green matrix CI across Python (ruff + mypy + pytest), Foundry (forge build + test + fmt), and Node (tsc + next build).

Total scan: ~5 minutes. If a reviewer hits step 5 and the badge is green, they've already decided to talk.

---

## The skill stack

The project is designed to demonstrate four layers most Web3 engineers cannot ship together:

| Layer                                     | Tech                                                             | Why it matters                                                                          |
| ----------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Financial-grade ledger**                | Python · FastAPI · Postgres event store · hexagonal architecture | Double-entry accounting, deterministic replay, idempotency — regulated-fintech baseline |
| **On-chain certificates of authenticity** | Solidity · Foundry · ERC-721 · IPFS                              | RWA tokenisation pattern: physical asset ↔ cryptographic ownership proof                |
| **Escrow lifecycle + vault attestation**  | State-machine domain layer · HMAC-signed webhooks                | The custody-handoff problem most RWA platforms hand-wave                                |
| **Audit-grade observability**             | Append-only event store · signed audit exports · structured logs | The compliance posture serious fintech reviewers actually look for                      |

---

## Architecture in one diagram

```
   ┌──────────────────────────────────────────────────────────────┐
   │   Next.js admin dashboard   │   Vault operator (HMAC POST)   │
   └──────────────┬───────────────┴───────────────┬───────────────┘
                  │ JWT                            │ HMAC-signed body
                  ▼                                ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                  FastAPI HTTP surface (11 endpoints)         │
   │  RFC 7807 errors  ·  Idempotency-Key  ·  CORS  ·  /docs      │
   ├──────────────────────────────────────────────────────────────┤
   │                   Application use-cases layer                │
   │   register_user · approve_kyc · deposit · register_asset     │
   │   open_escrow · lock_funds · record_vault_attestation        │
   │   mint_certificate · release_escrow                          │
   ├──────────────────────────────────────────────────────────────┤
   │  Domain layer (pure Python, zero framework imports)          │
   │  User · Asset · Escrow · Certificate · VaultAttestation      │
   │  13 events · 6 value objects · 7-state escrow machine        │
   ├──────────────────────────────────────────────────────────────┤
   │   Postgres event store        Base Sepolia contract          │
   │   single-table, append-only   ERC-721 with attestation gate  │
   │   replay → projections        verified on Basescan           │
   └──────────────────────────────────────────────────────────────┘
```

Full mermaid version + state machine + schema in [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

---

## Stack at a glance

| Layer          | Choice                                                                                         |
| -------------- | ---------------------------------------------------------------------------------------------- |
| Smart contract | Solidity 0.8.28 · Foundry · OpenZeppelin ERC-721 + AccessControl + Pausable                    |
| Backend        | Python 3.12 · FastAPI · SQLAlchemy 2 (async) · Pydantic v2 · Alembic · python-jose · structlog |
| Frontend       | Next.js 16 (App Router) · React 19 · TypeScript strict · Tailwind 4 oklch tokens               |
| Database       | Postgres 16 (event store + projections)                                                        |
| Chain          | Base Sepolia (Coinbase L2) · Alchemy / CDP RPC · Basescan verification                         |
| Storage        | IPFS via Pinata for certificate metadata                                                       |
| Tests          | pytest + testcontainers for backend · Foundry forge for contracts · Playwright for E2E         |
| CI             | GitHub Actions matrix (Python + Foundry + Node)                                                |
| Deploy         | Railway (backend + Postgres) · Vercel (frontend) · Foundry script (contract)                   |

---

## Run it locally

```powershell
# Backend (terminal 1)
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env   # then fill in JWT_SECRET, VAULT_HMAC_SECRETS
docker compose -f ..\docker-compose.yml up -d postgres
alembic upgrade head
uvicorn gemvault.main:app --reload --port 8000
# API: http://localhost:8000/docs

# Frontend (terminal 2)
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:3000

# Seed a full escrow lifecycle so the dashboard has data (terminal 3)
python scripts\demo\seed.py
```

---

## Deploy to production

End-to-end recipe in [`docs/DEPLOY.md`](./docs/DEPLOY.md):

- **Smart contract** — `gh workflow run deploy-contract.yml` (manual dispatch, runs Foundry on the GitHub runner with secrets)
- **Backend + Postgres** — Railway via the supplied `railway.toml` + Dockerfile
- **Frontend** — Vercel via `vercel --prod`
- **Demo data** — `python scripts/demo/seed.py` against the live backend
- **Demo GIF** — Playwright recording via `scripts/demo/record.spec.ts`

Cost estimate for the full live demo: **~$5/month** (Railway Hobby covers backend + Postgres; Vercel free tier; Base Sepolia is free).

---

## Decision artefacts

Everything load-bearing about why the project looks the way it does is captured in docs:

- [`docs/PRD-GEMVAULT.md`](./docs/PRD-GEMVAULT.md) — product spec + sprint plan + risks
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — system context, hexagonal layer, state machine, schema
- [`docs/adr/decisions.md`](./docs/adr/decisions.md) — four locked ADRs
- [`docs/openapi.yaml`](./docs/openapi.yaml) — full API surface
- [`docs/DEPLOY.md`](./docs/DEPLOY.md) — deploy guide
- [`docs/PIVOT-NOTE.md`](./docs/PIVOT-NOTE.md) — record of the pivot from an earlier direction (DeFi agent → RWA fintech). Historical artefacts in [`docs/archive/`](./docs/archive).

---

## Author

**Pyae Sone Kyaw** — Founder & AI Engineer at Ekkhara (Paris, Station F).

- Portfolio: [pseonkyaw.dev](https://pseonkyaw.dev)
- Dual Master's: Telecom SudParis + AIT
- 4+ years production AI/ML; 6+ products shipped end-to-end
- Adjacent regulated-grade work: VitaLens (AI lab-result interpretation), VitalAge (longitudinal health scoring), ComplyOS (EU AI Act compliance autopilot)

---

## License

MIT — see [`LICENSE`](./LICENSE).
