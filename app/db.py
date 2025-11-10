
import os
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./expenses.db")
database = Database(DATABASE_URL)
