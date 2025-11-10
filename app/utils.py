import json, os
from decimal import Decimal
from datetime import datetime

BRONZE_DIR = os.getenv("BRONZE_DIR", "./bronze")
os.makedirs(BRONZE_DIR, exist_ok=True)

# PoC conversion table; replace with real rates or service
RATES = {"USD": 1.0, "ZAR": 0.054, "EUR": 1.08}

# def save_raw(payload: dict, idempotency_key: str):
#     fname = f"{BRONZE_DIR}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{idempotency_key}.json"
#     with open(fname, "w", encoding="utf-8") as f:
#         json.dump(payload, f, default=str)
#     return fname

def save_raw(payload: dict, idempotency_key: str):
    fname = f"{BRONZE_DIR}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{idempotency_key}.json"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(payload, f, default=str)
        print("save_raw wrote", fname)
    except Exception as e:
        print("save_raw error:", e)
        raise
    return fname


def convert_to_usd(amount: float, currency: str) -> float:
    rate = RATES.get(currency.upper())
    if not rate:
        # if unknown currency, treat as zero or raise; here we fallback to 1.0
        rate = 1.0
    return float(Decimal(amount) * Decimal(rate))
