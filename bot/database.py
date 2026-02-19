import asyncpg
from bot.config import DATABASE_URL

async def create_pool():
    return await asyncpg.create_pool(DATABASE_URL)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE,
    city TEXT NOT NULL,
    address TEXT NOT NULL,
    rent INTEGER NOT NULL,
    bedrooms INTEGER NOT NULL,
    bathrooms INTEGER NOT NULL,
    size TEXT NOT NULL,
    furnished BOOLEAN NOT NULL,
    pets BOOLEAN NOT NULL,
    smoking BOOLEAN NOT NULL,
    available_date TEXT NOT NULL,
    phone TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
