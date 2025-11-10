import os
import sqlalchemy
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from redis.asyncio import Redis

from .schemas import ReceiptIn, ExpenseOut
from .db import database
from .models import metadata
from .worker import process_receipt

app = FastAPI(title="Travel Expense API")

# Simple in-memory idempotency store for PoC
IDEMPOTENT_STORE: dict = {}

REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)


@app.on_event("startup")
async def startup():
    # connect database (async)
    await database.connect()

    # create tables in dev (use migrations in prod)
    # Build a sync SQLAlchemy engine from DATABASE_URL so metadata.create_all can run
    sync_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./expenses.db")
    if sync_db_url.startswith("sqlite+aiosqlite"):
        sync_db_url = sync_db_url.replace("sqlite+aiosqlite", "sqlite")
    connect_args = {}
    if sync_db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = sqlalchemy.create_engine(sync_db_url, connect_args=connect_args)
    metadata.create_all(bind=engine)

    # connect to Redis if configured (optional)
    if REDIS_URL:
        try:
            app.state.redis = Redis.from_url(REDIS_URL, decode_responses=True)
            await app.state.redis.ping()
        except Exception:
            # fallback to no redis if unreachable
            try:
                await app.state.redis.close()
            except Exception:
                pass
            app.state.redis = None
    else:
        app.state.redis = None


@app.on_event("shutdown")
async def shutdown():
    # disconnect database
    await database.disconnect()

    # close redis if opened
    if getattr(app.state, "redis", None):
        await app.state.redis.close()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ingest/receipt", status_code=202)
async def ingest_receipt(receipt: ReceiptIn, background_tasks: BackgroundTasks):
    key = receipt.idempotency_key

    # check idempotency in Redis (preferred) then local store
    if getattr(app.state, "redis", None):
        exists = await app.state.redis.get(key)
        if exists:
            return {"status": "accepted", "message": "already processed"}
        # reserve key with TTL (1 hour)
        await app.state.redis.set(key, "processing", ex=60 * 60)
    else:
        if key in IDEMPOTENT_STORE:
            return {"status": "accepted", "message": "already processed"}
        IDEMPOTENT_STORE[key] = "processing"

    # enqueue background processing
    background_tasks.add_task(process_receipt, receipt.dict())
    return {"status": "accepted", "idempotency_key": key}


@app.get("/expenses", response_model=list[ExpenseOut])
async def get_expenses(
    user_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    if user_id:
        rows = await database.fetch_all(
            "SELECT * FROM expenses WHERE user_id = :user_id LIMIT :limit OFFSET :offset",
            values={"user_id": user_id, "limit": limit, "offset": offset},
        )
    else:
        rows = await database.fetch_all(
            "SELECT * FROM expenses LIMIT :limit OFFSET :offset",
            values={"limit": limit, "offset": offset},
        )
    return [dict(r) for r in rows]


@app.get("/reports/daily_revenue")
async def daily_revenue(date: str):
    q = "SELECT SUM(amount_usd) as total_usd FROM expenses WHERE DATE(timestamp) = :date"
    row = await database.fetch_one(q, values={"date": date})
    return {"date": date, "total_usd": row["total_usd"] or 0.0}
