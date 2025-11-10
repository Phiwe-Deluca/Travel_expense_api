from sqlalchemy import Table, Column, Integer, String, Float, DateTime, MetaData

metadata = MetaData()

expenses = Table(
    "expenses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("vendor", String),
    Column("amount", Float, nullable=False),
    Column("currency", String, nullable=False),
    Column("amount_usd", Float, nullable=False),
)
