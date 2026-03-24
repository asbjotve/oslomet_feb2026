import pymysql
import aiomysql
import asyncio
from config.config import settings
from typing import AsyncGenerator, Tuple, Any


DB_CONFIG = {
    "host": settings.DB_HOST,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "db": settings.DB_NAME,
    "autocommit": False,
}

_async_pool: aiomysql.Pool | None = None
_pool_lock = asyncio.Lock()

def get_db_config():
    return DB_CONFIG.copy()

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

async def get_async_db_pool() -> aiomysql.Pool:
    """
    Returnerer en global/singleton aiomysql pool.
    Opprettes kun én gang og gjenbrukes for alle requests.
    """
    global _async_pool

    if _async_pool is not None:
        return _async_pool

    async with _pool_lock:
        # Double-check etter lock (for concurrency)
        if _async_pool is None:
            _async_pool = await aiomysql.create_pool(**DB_CONFIG)

    return _async_pool

async def close_async_db_pool() -> None:
    """
    Lukker global pool (kalles ved app shutdown).
    """
    global _async_pool
    if _async_pool is None:
        return

    _async_pool.close()
    await _async_pool.wait_closed()
    _async_pool = None

async def get_db_conn_and_cursor() -> AsyncGenerator[Tuple[Any, Any], None]:
    """
    FastAPI dependency:
    Gir (conn, cursor) per request og returnerer conn til pool når request er ferdig.
    """
    pool = await get_async_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            yield conn, cursor
