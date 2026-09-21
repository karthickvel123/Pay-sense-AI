import aiosqlite
import asyncio
from typing import Any, List, Optional, Dict
from app.config import settings

# Parse simple sqlite url format or use default
DB_PATH = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
if not DB_PATH.endswith(".db"):
    DB_PATH = "./paysense.db"


async def get_db() -> aiosqlite.Connection:
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def execute_query(query: str, params: tuple = ()) -> int:
    """Execute a query and return the lastrowid."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.lastrowid


async def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Fetch all rows from a query."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Fetch a single row from a query."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def init_db():
    """Initialize the database tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                razorpay_order_id TEXT,
                razorpay_payment_id TEXT,
                amount INTEGER,
                currency TEXT DEFAULT 'INR',
                status TEXT,
                method TEXT,
                failure_reason TEXT,
                error_code TEXT,
                customer_email TEXT,
                customer_phone TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type TEXT,
                input_context TEXT,
                reasoning TEXT,
                action_taken TEXT,
                result TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS revenue_leaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leak_type TEXT,
                payment_id TEXT,
                amount_lost INTEGER,
                root_cause TEXT,
                recovery_suggestion TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(payment_id) REFERENCES payments(id)
            )
        ''')
        await db.commit()
