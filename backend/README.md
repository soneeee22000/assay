# Assay Backend

Python 3.12 · FastAPI · Postgres · SQLAlchemy · Pydantic v2 · pytest

Hexagonal architecture per [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md). Domain layer is framework-free.

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"

cp .env.example .env                                  # then fill in real values
pytest                                                # smoke test should pass
uvicorn assay.main:app --reload                    # http://localhost:8000/health
```

Open API docs at `http://localhost:8000/docs` when the server is running.

## Layout

```
src/assay/
├── domain/        Entities, events, value objects (no framework imports)
├── application/   Use-cases that orchestrate domain + adapters
├── adapters/      Driver (in) and driven (out) — FastAPI, Postgres, Base RPC, IPFS, auth
└── main.py        FastAPI app entrypoint

tests/
├── domain/        Pure unit tests, no DB
├── application/   Use-case tests with in-memory adapters
└── adapters/      Integration tests against real Postgres (testcontainers) and Anvil
```

## Conventions

- Strict mypy (`mypy src`)
- Ruff linting (`ruff check src tests`)
- 80%+ test coverage enforced in pytest config
- No `Optional` without a reason; prefer explicit defaults
- Decimal for USDC; never float
- Structured logging with `correlation_id` injected per request

## Running tests against a real Postgres

The integration test suite uses [testcontainers](https://testcontainers.com/) to spin up a real Postgres for each session. Docker must be running locally.

```bash
pytest tests/adapters/persistence/   # spins up Postgres, runs migrations, tears down
```

(Per session feedback: mocking the DB hides too many bugs. Integration tests hit a real Postgres.)
