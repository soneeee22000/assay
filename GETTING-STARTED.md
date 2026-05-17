# Getting Started — Local Development

Step-by-step runbook to get Assay running on your machine in ~10 minutes. No external API keys required — the chain layer is stubbed locally.

> **You'll end with:** Backend on `http://localhost:8000/docs`, dashboard on `http://localhost:3000`, real Postgres in Docker, an admin user signed in, and one full escrow lifecycle visible in the Ledger / Escrows / Certificates views.

---

## What you already have ✅

These are already set up from earlier in the session — you can skip to **Step 1** if you trust this list:

- ✅ Python 3.12 venv at `C:\Web3-BlockChain\backend\.venv`
- ✅ All Python dependencies installed (`fastapi`, `sqlalchemy`, `pytest`, etc.)
- ✅ Node 24 + npm 11 + `frontend/node_modules` populated
- ✅ Generated dev secrets in `backend/.env` (gitignored)
- ✅ Frontend env in `frontend/.env.local` (gitignored)
- ✅ The repo's `docker-compose.yml` defines a Postgres service

If any of those are missing, the **First-time setup** section at the bottom covers them.

---

## Step 1 — Start Docker Desktop

Assay uses real Postgres locally (per the global "no mocks" rule).

**Action on your end:**

1. Open the Windows Start menu → type `Docker Desktop` → click it.
2. Wait for the whale icon in the taskbar to stop animating (~30s on a cold start).
3. Verify in a PowerShell terminal:
   ```powershell
   docker ps
   ```
   You should see an empty container list, not an error.

If `docker ps` errors with `pipe/docker_engine: The system cannot find the file specified`, Docker Desktop isn't fully up yet — wait another 20s and retry.

---

## Step 2 — Start Postgres

```powershell
cd C:\Web3-BlockChain
docker compose up postgres -d
```

Expected output: `Container assay-postgres  Started`. The first run pulls the `postgres:16-alpine` image (~80 MB, ~30s).

Verify it's listening:

```powershell
docker compose ps
```

You should see `assay-postgres ... running ... healthy ... 0.0.0.0:5433->5432/tcp`.

> **Why 5433 and not 5432?** If you already have a native PostgreSQL service on your machine (Windows often does), it owns `localhost:5432` and Docker's `127.0.0.1` connections won't reach our container. We bind Docker to `5433` to side-step the collision. If you don't have a native Postgres you can change `docker-compose.yml` back to `"5432:5432"` and `backend/.env`'s `DATABASE_URL` port accordingly.

---

## Step 3 — Apply the database schema

The Alembic migration creates seven tables (`events`, `users`, `assets`, `escrows`, `certificates`, `vault_attestations`, `ledger_entries`).

```powershell
cd C:\Web3-BlockChain\backend
.venv\Scripts\activate
alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema
```

If you see `ModuleNotFoundError: assay`, re-run `pip install -e ".[dev]"` from `backend/`.

---

## Step 4 — Start the backend

In the same terminal (still in `backend/`):

```powershell
uvicorn assay.main:app --reload --port 8000
```

Expected output:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Open `http://localhost:8000/docs` — you should see the OpenAPI explorer with 11 endpoints under `auth`, `users`, `assets`, `escrows`, `vault`, `audit`, plus a `meta /health`.

Quick sanity check from another terminal:

```powershell
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

**Leave this terminal running.** Open a new one for the next steps.

---

## Step 5 — Seed a full escrow lifecycle

The seed script registers an admin + buyer + seller, approves their KYC, deposits 500 USDC into the buyer's balance, registers a gold-bar asset to the seller, opens an escrow for 100 USDC, and drives it all the way through to `RELEASED`.

In a **new** PowerShell terminal:

```powershell
cd C:\Web3-BlockChain
.\backend\.venv\Scripts\activate
# One-time: install the sync Postgres driver the seed uses to bump admin KYC.
pip install "psycopg[binary]"

$env:DATABASE_URL_SYNC = "postgresql://assay:assay@localhost:5433/assay"
$env:VAULT_HMAC_SECRET = "sr0_7ZAPtQ2RqrjD88oZYwY4FFw2hZON21bCk_ai5FE"
$env:VAULT_OPERATOR_ID = "vault-local-01"
python scripts\demo\seed.py
```

Expected output:

```
→ Register admin admin@example.com
→ Sign in as admin@example.com
→ Register buyer + seller
→ Approve KYC for buyer + seller
→ Fund the buyer with 500 USDC
→ Register a gold-bar asset to the seller
→ Open an escrow for 100 USDC
→ Lock funds
→ Vault attestation (HMAC-signed webhook)
→ Mint certificate
→ Release escrow
✓ Escrow <uuid> reached RELEASED
```

The seed script is idempotent for users (running it twice just adds a new escrow). The admin credentials are:

- Email: `admin@example.com`
- Password: `adminpass1234`

---

## Step 6 — Start the frontend

In **another** new terminal:

```powershell
cd C:\Web3-BlockChain\frontend
npm run dev
```

Expected output:

```
  ▲ Next.js 16.2.6 (Turbopack)
  - Local:        http://localhost:3000
  - ready in 2.1s
```

Open `http://localhost:3000`. You should see the green "Backend healthy · v0.1.0" badge.

---

## Step 7 — Sign in and click around

1. Click **Sign in** (or visit `http://localhost:3000/login` directly).
2. Email: `admin@example.com`, Password: `adminpass1234` → click **Sign in**.
3. You land on `/ledger`. You should see ~10 events from the seed run.
4. Click **Escrows** in the nav → one escrow card with state `RELEASED`.
5. Click the escrow ID → detail view with a full 5-step timeline (Opened → Funds locked → Vault attested → Certificate minted → Released).
6. Click **Certificates** → one minted certificate with placeholder Basescan and IPFS link-outs.

**That's the full demo flow working locally.** Run `python scripts\demo\seed.py` again to add another escrow — the views auto-show it (the 24-hour audit window is hard-coded).

---

## Stopping everything

When you're done:

```powershell
# Terminal 1 (backend):  Ctrl+C
# Terminal 2 (seed):     already exited
# Terminal 3 (frontend): Ctrl+C

# Stop Postgres (data persists in the volume):
cd C:\Web3-BlockChain
docker compose stop postgres

# Or wipe everything including data:
docker compose down -v
```

Next start-up only needs Steps 1, 2, 4, 6 (Postgres + backend + frontend). Schema and seed data persist across restarts.

---

## What to do when something breaks

| Symptom                                                      | Cause / Fix                                                                                           |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `docker ps` says "daemon not running"                        | Docker Desktop isn't up yet. Click the taskbar icon and wait 30s.                                     |
| `alembic upgrade head` says `ModuleNotFoundError: assay`  | Reinstall the package: `cd backend && .venv\Scripts\activate && pip install -e ".[dev]"`              |
| `uvicorn` says `port already in use`                         | Another process holds :8000. Find it: `netstat -ano \| findstr :8000`, kill via Task Manager.         |
| Frontend home page shows the red "Backend unreachable" badge | Backend not running, or CORS broken. Confirm `curl http://localhost:8000/health` works first.         |
| Seed script says `401 unknown user or no password set`       | The schema is stale. Run `alembic upgrade head` again, then re-run the seed.                          |
| Ledger view shows "No events in the last 24 hours"           | Seed hasn't been run yet, or the system clock is way off. Re-run `python scripts\demo\seed.py`.       |
| Sign-in says `password mismatch`                             | You're trying to sign in as a user the seed didn't create. Use `admin@example.com` / `adminpass1234`. |

---

## What's NEXT (after local works)

When you've got the dashboard clicking through locally and want to ship a live URL, see **[`docs/DEPLOY.md`](./docs/DEPLOY.md)**. That guide walks through:

1. Deploying the Solidity contract to Base Sepolia via the GitHub Action (needs three repo secrets — see "External services" below).
2. Deploying the backend to Railway (~5 min, $5/mo).
3. Deploying the frontend to Vercel (~3 min, free).
4. Recording the demo GIF via Playwright (`scripts/demo/record.spec.ts`).
5. Pasting the live URLs into the README.

---

## External services (only needed for production, NOT for local)

The local stack uses `StubChainClient` and doesn't talk to any external service. You can ship the entire local demo without signing up for anything. The signups below are only relevant when you move to live deploy.

| Service                         | Why                                | Where to sign up                                                     |
| ------------------------------- | ---------------------------------- | -------------------------------------------------------------------- |
| **Alchemy** (or Coinbase CDP)   | Base Sepolia RPC + on-chain notify | <https://www.alchemy.com/> · free tier, email only, no credit card   |
| **Coinbase Developer Platform** | ERC-4337 smart-wallet operations   | <https://portal.cdp.coinbase.com/> · email signup, no KYC            |
| **Basescan API**                | Contract verification + tx reads   | <https://basescan.org/myapikey> · free email signup                  |
| **Pinata** (IPFS)               | Certificate metadata pinning       | <https://app.pinata.cloud/> · free tier 1 GB / 100 pins              |
| **Base Sepolia faucet**         | Test ETH for the deployer EOA      | <https://portal.cdp.coinbase.com/products/faucet> · 0.05–0.1 ETH/day |
| **Railway**                     | Backend + Postgres hosting         | <https://railway.app/> · $5/mo Hobby plan covers both                |
| **Vercel**                      | Frontend hosting                   | <https://vercel.com/> · free tier                                    |

The deploy recipe in `docs/DEPLOY.md` tells you exactly which env var each provided key fills.

---

## First-time setup (only if you're missing the venv / node_modules)

If the "What you already have" section was missing things — e.g. fresh machine, fresh clone — these are the one-time install commands:

```powershell
# Python venv
cd C:\Web3-BlockChain\backend
C:\Users\pyaes\.local\bin\python3.12.exe -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# Node modules
cd ..\frontend
npm install

# Confirm everything works
cd ..\backend
.venv\Scripts\activate
pytest --no-cov     # should report 91 passed, 22 skipped (Docker-dependent)
cd ..\frontend
npm run typecheck   # should report no errors
```

Then loop back to **Step 1**.
