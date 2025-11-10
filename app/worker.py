from .utils import convert_to_usd, save_raw
from .crud import insert_expense
from datetime import datetime
import asyncio

async def process_receipt(payload: dict):
    # save bronze
    save_raw(payload, payload["idempotency_key"])
    # cleaning / normalization
    rec = {
        "user_id": payload["user_id"],
        "timestamp": payload["timestamp"],
        "vendor": payload.get("vendor"),
        "total": payload["total"],
        "currency": payload["currency"],
    }
    # convert
    rec["amount_usd"] = convert_to_usd(rec["total"], rec["currency"])
    # insert into silver (DB)
    await insert_expense(rec)
