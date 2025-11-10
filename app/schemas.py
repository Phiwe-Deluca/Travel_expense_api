from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import date, datetime

class ReceiptLine(BaseModel):
    description: Optional[str]
    amount: float
    currency: str

class ReceiptIn(BaseModel):
    idempotency_key: str = Field(..., min_length=8)
    user_id: str
    timestamp: datetime
    vendor: Optional[str]
    currency: str
    total: float
    lines: list[ReceiptLine]

class ExpenseOut(BaseModel):
    id: int
    user_id: str
    timestamp: datetime
    vendor: Optional[str]
    amount_usd: float
    currency: str
