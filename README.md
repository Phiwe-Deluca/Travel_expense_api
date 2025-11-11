# Travel Expense API

A lightweight FastAPI service for ingesting and querying travel expenses. Features idempotent receipt ingestion, bronze file persistence, PostgreSQL raw shards, SQLite aggregated shards, and ready-to-deploy Docker + Cloud Run CI/CD.

---

## Features
- REST endpoints for ingesting receipts and querying user expenses  
- Idempotency support (idempotency key via Redis)  
- Writes raw events to bronze files and sharded Postgres tables (tablename_YYYYMMDD)  
- Aggregation pipeline that reads raw shards, creates daily aggregated metrics and writes sharded SQLite tables (sales_aggregated_YYYYMMDD)  
- Dockerfile for Cloud Run and GitHub Actions workflow for CI/CD deployment

---

## Quickstart (local development)

Prerequisites
- Python 3.10+  
- PostgreSQL (or Docker)  
- Redis (or Docker)  
- git, Docker (optional for containerized runs)

1. Clone the repo
```bash
git clone <repo-url>
cd <repo-dir>
```

2. Create and activate a Python virtualenv
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Create local DB and Redis (choose one)
- Local Postgres (manual) or start with Docker Compose:
```bash
docker-compose up -d   # starts app dependencies (postgres, redis) if provided
```

4. Set environment variables (example .env)
```bash
cp .env.example .env
# Edit .env: DATABASE_URL, REDIS_URL, ENV, etc.
```

5. Run the app
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

6. Smoke test (after server starts)
```bash
curl -sS http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/ingest/receipt \
  -H "Content-Type: application/json" \
  -d '{"idempotency_key":"smoke-001","user_id":"simphiwe","timestamp":"2025-11-10T12:00:00Z","vendor":"Smoke","currency":"ZAR","total":1,"lines":[]}'
curl "http://127.0.0.1:8000/expenses?user_id=simphiwe"
```

---

## Endpoints

GET /health
- Returns service health.

POST /ingest/receipt
- Body: JSON receipt payload (includes **idempotency_key**, **user_id**, **timestamp**, **vendor**, **currency**, **total**, **lines**, etc.)
- Behavior: validates payload, uses Redis-backed idempotency key to prevent double-processing, writes to bronze file, enqueues worker for DB persistence.

GET /expenses
- Query params: user_id (required), date_from, date_to, limit, offset
- Behavior: returns user expense records or aggregated metrics.

(See API docs at /docs when server is running.)

---

## Storage and Sharding

- Bronze: local directory (./bronze) where raw JSON lines are appended for each ingest  
- Postgres: raw sharded tables named as base_YYYYMMDD (e.g., users_20251111) for historical raw copies  
- SQLite: aggregated sharded tables named sales_aggregated_YYYYMMDD for analyst use

Schema checks are applied before writing raw data to Postgres. Aggregation is performed by reading today's shard tables.

---

## Docker & Cloud Run

Dockerfile included at repo root. Image listens on $PORT (8080). Example Docker build:
```bash
docker build -t travel-api:dev .
docker run -e DATABASE_URL=<db> -e REDIS_URL=<redis> -p 8000:8080 travel-api:dev
```

Cloud Run CI/CD
- Workflow: .github/workflows/deploy-cloudrun.yml (builds image, pushes to registry, deploys to Cloud Run)
- Required GitHub Secrets:
  - GCP_PROJECT, GCP_REGION, GCP_SA_KEY, DATABASE_URL, REDIS_URL
- Service account must have Cloud Run Admin and registry/push roles.

---

## Environment variables

- DATABASE_URL — SQLAlchemy-style URL for Postgres (postgresql+psycopg2://user:pass@host:5432/db)  
- REDIS_URL — Redis connection (redis://host:port)  
- ENV — development | production  
- BRONZE_DIR — path to bronze files (default ./bronze)  
- LOG_LEVEL — info | debug

Store secrets in Secret Manager (Cloud Run) for production; use .env locally.

---

## Testing

- Unit tests in tests/ (pytest)
```bash
pip install -r requirements-dev.txt
pytest -q
```
- Add integration tests that spin up Postgres and Redis (docker-compose) and run end-to-end ingest -> read flows.

---

## Troubleshooting

- ModuleNotFoundError after pip installs: restart kernel / virtualenv and re-run imports.  
- NameError for variables: ensure extract functions run before using DataFrames (run cells in order).  
- Postgres connection refused: confirm DB is running and DATABASE_URL points to correct host/port and user.  
- Idempotency issues: verify Redis reachable and idempotency TTL settings in config.

---

## Contributing

- Fork, create a feature branch, open a PR against main.  
- Include tests and update README when adding features.  
- Keep API backwards-compatible or document breaking changes in changelog.

---

## Maintainers
- Simphiwe Moloi (lead developer) — project owner and main point for architecture/design decisions.

---

## License
MIT License — see LICENSE file for details.
