from .models import expenses
from .db import database
from datetime import datetime

async def insert_expense(rec):
    query = expenses.insert().values(
        user_id=rec["user_id"],
        timestamp=rec["timestamp"],
        vendor=rec.get("vendor"),
        amount=rec["total"],
        currency=rec["currency"],
        amount_usd=rec["amount_usd"],
    )
    return await database.execute(query)

async def list_expenses(user_id: str = None, start: str = None, end: str = None, limit: int = 100, offset: int = 0):
    q = expenses.select()
    if user_id:
        q = q.where(expenses.c.user_id == user_id)
    if start:
        q = q.where(expenses.c.timestamp >= start)
    if end:
        q = q.where(expenses.c.timestamp <= end)
    q = q.limit(limit).offset(offset)
    return await database.fetch_all(q)
