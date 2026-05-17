# Architecture Decision Records

Format: each ADR captures one architectural decision with context, the alternatives considered, the choice made, and the consequences. ADRs are immutable once accepted — superseded by new ADRs, never edited.

---

## ADR-001 — ERC-721 (1-of-1) over ERC-3525 (semi-fungible)

**Status:** Accepted · 2026-05-11
**Context:** Each physical asset (a precious-metal bar) in the platform has a unique assay certificate number and a unique provenance record. The question is whether to model on-chain certificates as fully unique tokens (ERC-721), semi-fungible classes (ERC-3525), or fungible batches (ERC-1155).

**Decision:** ERC-721. One token per certificate, strict 1-of-1.

**Alternatives considered:**

- **ERC-3525 (semi-fungible token).** Lets us group certificates by fineness-grade bucket or asset class for partial-share fractional ownership. Rejected for v1: fractional ownership is explicitly out of scope per PRD, and the standard adds tooling complexity (wallets and explorers handle ERC-3525 inconsistently).
- **ERC-1155 (multi-token).** Lets us batch-mint fungible classes plus 1-of-1 NFTs in one contract. Rejected: the certification model is inherently unique per asset; batching is a feature for utility tokens, not certificates of authenticity.
- **A custom non-standard contract.** Rejected outright — interoperability with marketplaces, indexers, and wallets is critical even for a portfolio piece.

**Consequences:**

- Simpler tooling: OpenZeppelin ERC-721 + Foundry forge-std cover 95% of what we need
- Loses the ability to fractionalise without a wrapper contract — acceptable since fractionalisation is a Phase-2 concern, not Phase-1
- If we later want fractional ownership, the migration is "deploy a fractionaliser that takes ERC-721 → mints ERC-20 shares" — well-trodden pattern, no need to lock it in now

---

## ADR-002 — Off-chain HMAC webhook + on-chain admin relay for vault attestation

**Status:** Accepted · 2026-05-11
**Context:** When a vault confirms it has taken physical custody of an asset, the platform must record an attestation that gates the on-chain certificate transfer. The vault operator may be a real-world custodian (Brink's, Loomis, Malca-Amit) with zero crypto-native infrastructure. The decision is how the attestation reaches the chain.

**Decision:** Vault operator HMAC-signs a JSON webhook payload. Our backend verifies HMAC + nonce, persists the attestation event, then calls `attestVault(tokenId, vaultRef)` on the contract using the platform's authorised admin key.

**Alternatives considered:**

- **On-chain EIP-712 signed message from vault operator's own wallet.** More crypto-pure: no trust in our backend to faithfully forward. Rejected: requires every vault operator to hold a funded Base wallet, manage gas, understand transaction signing. This is an integration deal-breaker for real custodians — they already refuse to integrate with crypto-native systems for this exact reason.
- **Vault operator triggers a meta-transaction relayer.** Same trust-minimisation as EIP-712 but we pay gas. Rejected: still requires the vault to sign EIP-712 payloads, which is the actual integration friction.
- **Our backend fully synthesises attestations with no vault input.** Rejected — would defeat the whole point. We need a verifiable signal that the vault confirmed.

**Consequences:**

- Trust assumption: the platform's admin key faithfully relays vault webhooks to the chain. Acceptable for v1 with the key under multisig in production.
- Gas paid by the platform, not the vault. Better partner UX, slightly higher operational cost (negligible on Base).
- Vault operators integrate with a 50-line HTTP client + shared secret. No crypto knowledge required.
- Replay protection: `(operator_id, nonce)` unique constraint at the DB layer.
- Signature scheme: HMAC-SHA256 over the raw request body, base64-encoded, sent in `X-Assay-Signature` header.

---

## ADR-003 — Single events table with stream discriminator (not per-aggregate streams)

**Status:** Accepted · 2026-05-11
**Context:** Event-sourced systems typically use either (a) one events table with a `stream_id` discriminator or (b) one table per aggregate type. The classical event-store.com style uses per-aggregate streams; the simpler pattern uses a single table.

**Decision:** Single `events` table with `stream_id` + `stream_type` + sequential `version` per stream.

**Alternatives considered:**

- **Per-aggregate stream tables (`user_events`, `escrow_events`, `certificate_events`).** More orthodox; each table optimisable independently; better isolation for partitioning. Rejected for v1: 3× the migration surface for negligible gain at the scale this project will ever reach. Pattern is well-understood enough that a future migration is a 1-day job if scale demands it.
- **An external event-store product (EventStoreDB, Marten, AxonIQ).** Rejected: introduces a separate piece of infrastructure to host and learn. Postgres handles the workload easily.
- **CDC from a state table into an event log.** Rejected — backwards: state is _derived from_ events, not the other way around. CDC fits very different problems.

**Consequences:**

- All events live in one table. Indexed on `(stream_id, version)` for fast aggregate reload, on `correlation_id` for cross-stream tracing, on `ts` for time-range queries.
- Unique constraint on `(stream_id, version)` enforces optimistic concurrency — concurrent writes to the same aggregate conflict at the DB layer.
- Read-model projections rebuilt by replaying events from this table. Replay is a cold operation; we don't optimise for it yet.
- Future migration path: split by `stream_type` into separate tables if a single table becomes a hotspot. No schema change to the events themselves.

---

## ADR-004 — Stub JWT auth with explicit integration point for Clerk/Auth0/Supabase

**Status:** Accepted · 2026-05-11
**Context:** The platform needs auth for the admin dashboard and for the user-facing REST endpoints. Real auth-provider integration takes 1-2 days and adds a third-party dependency. For a portfolio piece, the value of that integration is signalling polish more than proving the architecture.

**Decision:** Use a stubbed JWT auth layer: HMAC-signed JWTs issued by a single `POST /auth/login` endpoint that checks email + password against a `users` table. The auth verifier middleware is wired through a clean port so swapping in Clerk or Auth0 is a one-file change.

**Alternatives considered:**

- **Wire up Clerk (or Auth0, or Supabase Auth) end-to-end.** More polished. Rejected for v1: 1-2 days of integration work, an extra signup path for reviewers to clone the repo (less friction wins), and an extra service to fail in the demo.
- **No auth at all (open admin endpoints).** Rejected — looks careless on a fintech-themed project. Auth IS the conversation in regulated-grade systems.
- **OAuth via GitHub / Google.** Rejected — also adds a signup-friction story for reviewers and doesn't fit the user model (real users are not necessarily GitHub-savvy).

**Consequences:**

- Reviewers can run the demo without signing up for anything. Email + password creates a local user.
- The integration point for a real provider is visible in `src/adapters/auth/` — clean port + adapter pattern.
- README explicitly states the stub is intentional and lists the production providers we would swap in.
- A reviewer who specifically wants to see real-auth experience can look at adjacent work (Ekkhara projects) instead of demanding it from this repo.

---

## Decisions deferred to implementation time

- **Foundry vs Hardhat for contracts.** Defaulting to Foundry because forge-std + fuzzing + invariants are best-in-class. If we hit a specific incompatibility with Coinbase tooling, revisit.
- **Pinata vs web3.storage for IPFS.** Defaulting to Pinata because the JWT auth is simpler. Switch if rate limits bite.
- **viem vs ethers.js in the frontend.** Defaulting to viem (smaller bundle, modern TS, better types). Revisit only if a needed wagmi hook hard-depends on ethers.

These are _implementation_ defaults, not _architectural_ ones — they can change in a PR without an ADR.
