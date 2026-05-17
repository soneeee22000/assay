# Assay — Product Requirements

**Codename:** Assay
**Status:** Spec locked 2026-05-11 · architecture next
**Target build window:** ~2 weeks (one focused builder)
**Positioning:** Reference RWA fintech architecture — physical asset (vaulted precious metals, with allocated gold and silver bullion as the worked example) tokenised as certificate-of-authenticity NFTs, settled through a custodian-backed escrow flow, on a financial-grade event-sourced ledger.

## Why this project exists

Most "Web3 portfolio" repos prove one skill: "I can write a Solidity contract" OR "I can integrate a wallet" OR "I can ship a dashboard." Almost none prove the layer the fintech-meets-RWA category actually needs: a clean, regulated-grade backend that owns the ledger, audit log, escrow lifecycle, AND the on-chain certification layer in one vertical slice.

Assay is that vertical slice. It is deliberately scoped so that a reviewer scanning the repo in five minutes can see all four layers (smart contract, ledger backend, audit trail, admin dashboard) and follow them end-to-end.

## Target reader (who this portfolio piece is for)

- Founders / early engineers at fintech-meets-RWA startups
- Hiring leads at digital-banking-plus-asset-tokenisation platforms
- Anyone who needs someone fluent across: regulated audit trails, double-entry ledgers, smart-contract minting, vault custody integration, mobile-first UX

## Non-goals

- Not a venture in itself — no GTM, no buyer acquisition, no production hardening beyond what the demo flow needs
- Not an attempt to compete with LBMA-accredited assayers — the on-chain cert is a _companion_ to the assay certificate, not a replacement
- Not a marketplace — secondary trading is out of scope (mintable + transferable is enough)
- Not a DeFi protocol — no AMM, no lending, no yield

## Three pillars (the slice we ship)

### Pillar 1 — On-chain Certificate of Authenticity (smart contract)

- Chain: Base Sepolia testnet
- Contract: ERC-721 (or ERC-3525 semi-fungible if multi-edition needed)
- Metadata: IPFS-pinned JSON containing certification fields (issuer, asset type, weight, grade, batch ID, vault custodian, photo hashes)
- Transfer hook: requires a `vaultAttested` flag set by an authorised vault operator address before transfer succeeds — proves the off-chain custody handoff happened
- Pause / unpause for emergency
- Verified on Basescan with full source visibility

### Pillar 2 — Financial-grade Ledger Backend (Python + FastAPI)

- Double-entry ledger backed by Postgres
- Event-sourced — every state change is an immutable append-only event; ledger state is a deterministic projection
- Domain events: `FundsDeposited`, `EscrowOpened`, `FundsLocked`, `VaultAttested`, `CertificateMinted`, `EscrowReleased`, `FundsWithdrawn`, `RefundIssued`
- KYC stub: lightweight `User.kyc_status` field with `PENDING / APPROVED / REJECTED` states, gated by an admin endpoint (not real KYC — placeholder to show the integration point)
- Webhook endpoint for vault operator to post attestation (with HMAC-signed request, replay protection)
- Stablecoin (USDC) accounting on a single chain — testnet, not real custody
- Audit log export: signed CSV of all events for a given period, replayable from event store

### Pillar 3 — Admin Dashboard (Next.js + shadcn)

- Mobile-first design (per the global Tailwind / shadcn standards)
- Three views:
  1. **Ledger** — table of all events, filterable by user / event type / date range
  2. **Certificates** — gallery of minted certs, with link to Basescan + IPFS
  3. **Escrows** — state machine visualisation per escrow (timeline view of `Opened → FundsLocked → VaultAttested → Released`)
- Read-only — no transaction signing in the dashboard; signing happens via the backend admin endpoints behind auth

## Hexagonal architecture (per global standards)

```
   ┌────────────────────────────────────────────────────────────────┐
   │                     Driver adapters (in)                       │
   │   FastAPI REST  ·  Next.js dashboard (HTTP)  ·  Vault webhook  │
   └───────────────────────────┬────────────────────────────────────┘
                               │
              ┌────────────────▼─────────────────┐
              │            Application           │
              │ Use-cases · Domain services      │
              │ (no framework or DB code here)   │
              └────────────────┬─────────────────┘
                               │
              ┌────────────────▼─────────────────┐
              │              Domain              │
              │ Entities · Events · Invariants   │
              │  Ledger · Escrow · Certificate   │
              └────────────────┬─────────────────┘
                               │
   ┌───────────────────────────▼────────────────────────────────────┐
   │                    Driven adapters (out)                       │
   │ Postgres event store · Base RPC · IPFS · HMAC vault verifier   │
   └────────────────────────────────────────────────────────────────┘
```

Domain layer is framework-free — pure Python, no FastAPI imports, no SQLAlchemy. Tests run in milliseconds without a DB.

## Compliance posture (what makes this "fintech-grade")

- Immutable event store — events are append-only, never updated or deleted
- Deterministic replay — ledger state can be rebuilt from the event store at any historic timestamp
- Signed audit exports — CSV exports include an HMAC of all events for tamper detection
- Idempotency keys on every state-changing endpoint
- Structured logging with correlation IDs across HTTP / DB / chain calls
- No PII in event payloads — only user IDs that resolve to a separate users table

## Stack

| Layer           | Choice                                                         | Why                                                                                    |
| --------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Chain           | Base Sepolia testnet                                           | Agent-native L2, cheap, fast, Coinbase tooling, matches RWA-fintech ecosystem traction |
| Smart contract  | Solidity 0.8.x, Foundry, ERC-721 (or ERC-3525)                 | Mature standard, well-audited templates exist (OpenZeppelin)                           |
| Backend         | Python 3.12 + FastAPI + SQLAlchemy + Pydantic v2 + pytest      | User's strongest production stack                                                      |
| Database        | Postgres 16 (event store + materialised views for projections) | Battle-tested for event-sourced systems                                                |
| Frontend        | Next.js 15 + React 19 + Tailwind 4 + shadcn/ui                 | Per global standards                                                                   |
| On-chain client | viem + web3.py (depending on the layer)                        | Modern TS, mature Python                                                               |
| IPFS            | Pinata or web3.storage free tier                               | No infra to run                                                                        |
| Tests           | pytest (Python) + Foundry (contracts) + Playwright (E2E)       | Per global TDD standards                                                               |
| Deploy          | Docker compose for local; Railway or Render for live demo URL  | Cheap, fast, no devops rabbit holes                                                    |

## Reviewer experience (the 5-minute path)

1. Open repo → README leads with: 30-second elevator pitch, demo video (GIF), live URL
2. Click live URL → admin dashboard loads on testnet data
3. Click "Mint demo certificate" → backend opens escrow, simulates vault attestation, mints ERC-721, displays cert
4. Click the certificate → link to Basescan (verified contract) + IPFS metadata
5. Open `docs/ARCHITECTURE.md` → see hexagonal diagram + ADR list
6. Open `tests/` → see 80%+ coverage, fast suite

If a reviewer hits step 6 and the suite is green, they've already decided to talk.

## Sprint plan

| Sprint   | Days | Deliverable                                                                                                           |
| -------- | ---- | --------------------------------------------------------------------------------------------------------------------- |
| Sprint 0 | 0.5d | Repo scaffold (Python project, Foundry init, Next.js init, Docker compose) · CI green · ADR-001 architecture          |
| Sprint 1 | 3d   | Domain layer: ledger + escrow + certificate entities, events, use-cases. 100% unit-tested. No framework dependencies. |
| Sprint 2 | 2d   | Postgres event-store adapter + projections. Integration tests against real Postgres (per global feedback memory).     |
| Sprint 3 | 2d   | Solidity certificate contract (ERC-721 with vault-attestation gate) + Foundry test suite + Basescan verification.     |
| Sprint 4 | 2d   | FastAPI REST surface + HMAC-protected vault webhook + signed audit-export endpoint.                                   |
| Sprint 5 | 2d   | Next.js admin dashboard (Ledger / Certificates / Escrows views) + Playwright E2E happy-path.                          |
| Sprint 6 | 1d   | Deploy to Railway (backend + Postgres) + Vercel (frontend) + record demo GIF + finalise README.                       |
| Sprint 7 | 0.5d | ADRs + ARCHITECTURE.md polish + add 5-minute reviewer path to README.                                                 |

Total: ~13 working days. Built-in slack for the unknown unknowns (likely on the contract verification + the vault attestation HMAC verifier).

## Risks

| Risk                                                     | Mitigation                                                                                                                                |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Solidity is new to me; contract takes longer than 2 days | Use OpenZeppelin templates and Foundry forge-std for test scaffolding; cap contract scope at "ERC-721 + vault-gate transfer hook + pause" |
| Event-sourcing without a framework can over-engineer     | Hand-rolled — single `EventStore` table with `(stream_id, version, event_type, payload_json, ts)`; no Kafka, no CQRS framework            |
| Vault webhook verification logic is non-trivial          | HMAC-SHA256 + nonce + Redis (or Postgres) replay-cache; ~50 lines, well-trodden                                                           |
| Dashboard scope creeps                                   | Lock to 3 views, read-only. No filters beyond the spec. No charts (text-first audit log is the point).                                    |
| Reviewer wants real KYC                                  | Out of scope — clearly noted as a stub with the integration point exposed (where Stripe Identity / Sumsub etc would plug in)              |

## What this is NOT showing (and is OK to leave out)

- Multi-chain — single chain (Base Sepolia) is enough
- Production-grade secrets management — `.env` is fine; reviewers know this is a portfolio piece
- Real KYC integration — stub is explicit and acceptable
- Multi-currency FX — USDC-only is fine
- Multi-tenant isolation — single-tenant test data is fine

## Open questions — RESOLVED in `docs/adr/decisions.md` (2026-05-11)

The four architecture-step questions have been settled. Summaries:

1. **ERC-721 vs ERC-3525** → ERC-721 (ADR-001). 1-of-1 cert per asset; fractionalisation is a Phase-2 concern with a known migration path.
2. **Vault attestation model** → Off-chain HMAC webhook + on-chain admin relay (ADR-002). Lets real-world custodians integrate without crypto wallets.
3. **Event store layout** → Single events table with stream discriminator (ADR-003). Migration to per-aggregate streams is a 1-day job if scale demands it.
4. **Auth provider** → Stub JWT with clean port for Clerk/Auth0 swap-in (ADR-004). Reviewers run the demo without third-party signup.

Original open-questions text retained below for traceability.

---

1. ERC-721 vs ERC-3525 — does the bullion domain need semi-fungible cert classes (e.g. 5 fineness-grade buckets) or strict 1-of-1?
2. Vault attestation: on-chain signed message or off-chain webhook + on-chain admin transaction? Tradeoff: trust assumption vs gas cost.
3. Event store: single table or per-aggregate streams? Single table is simpler; per-stream is more orthodox.
4. Auth: stub JWT in headers or wire up a real provider (Clerk / Supabase Auth)? Stub is faster; real provider signals more polish.

Next step: open `/architect` to resolve these and produce `docs/ARCHITECTURE.md`.
