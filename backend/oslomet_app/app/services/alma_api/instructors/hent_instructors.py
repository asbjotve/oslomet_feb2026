from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Any

import aiohttp
import aiomysql
import pymysql

from config.config import settings

logger = logging.getLogger(__name__)

API_TOKEN = settings.ALMA_API_KEY
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {API_TOKEN}",
}

# ---------------------------- Tuning knobs -----------------------------------
HTTP_CONCURRENCY = 25          # samtidige HTTP-kall
DB_CONCURRENCY = 10            # samtidige DB-writes (ofte lavere enn HTTP)
HTTP_PACING_SECONDS = 0.02     # liten pacing for å unngå bursts
MAX_ATTEMPTS_429 = 10
INITIAL_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 125.0
JITTER_SECONDS = 1.0
# -----------------------------------------------------------------------------


# ------------------------ Dedicated loggers ----------------------------------
LOG_BASE_DIR = "/home/ubuntu/github_oslomet_f2026/backend/oslomet_app/log/oslomet"
INSTR_429_LOG_PATH = f"{LOG_BASE_DIR}/alma_instructors_429.log"
INSTR_401873_LOG_PATH = f"{LOG_BASE_DIR}/alma_instructors_401873.log"


def _make_rotating_file_logger(name: str, path: str, level: int = logging.INFO) -> logging.Logger:
    lg = logging.getLogger(name)
    lg.setLevel(level)
    lg.propagate = False

    if not lg.handlers:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = RotatingFileHandler(path, maxBytes=10_000_000, backupCount=5)
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        lg.addHandler(fh)

    return lg


alma_instr_429_logger = _make_rotating_file_logger("alma429.instructors", INSTR_429_LOG_PATH, logging.INFO)
alma_instr_401873_logger = _make_rotating_file_logger("alma401873.instructors", INSTR_401873_LOG_PATH, logging.INFO)
# -----------------------------------------------------------------------------


def _parse_retry_after_seconds(resp: aiohttp.ClientResponse) -> float | None:
    ra = resp.headers.get("Retry-After")
    if not ra:
        return None
    try:
        return float(ra)
    except ValueError:
        return None


async def _sleep_backoff_with_jitter(
    attempt: int,
    *,
    base_delay: float,
    max_delay: float,
    jitter: float,
) -> None:
    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
    sleep_s = random.uniform(0, delay) + random.uniform(0, jitter)
    await asyncio.sleep(sleep_s)


def _body_one_line(text: str, limit: int = 200) -> str:
    return " ".join((text or "").split())[:limit]


def _extract_owner_names(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    owners = data.get("owner")
    if not owners:
        return ""
    if not isinstance(owners, list):
        return ""
    full_names = [o.get("full_name") for o in owners if isinstance(o, dict) and o.get("full_name")]
    return " ; ".join(full_names)


def _has_error_code_401873(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if not data.get("errorsExist"):
        return False
    errors = (data.get("errorList") or {}).get("error") or []
    if isinstance(errors, dict):
        errors = [errors]
    if not isinstance(errors, list):
        return False
    for err in errors:
        if isinstance(err, dict) and str(err.get("errorCode")) == "401873":
            return True
    return False


async def execute_with_retry(c: aiomysql.Cursor, sql: str, params: tuple, attempts: int = 5) -> None:
    """
    Retry for transient MySQL errors:
    - 1213 = deadlock
    - 1205 = lock wait timeout
    """
    for i in range(attempts):
        try:
            await c.execute(sql, params)
            return
        except pymysql.err.OperationalError as e:
            code = e.args[0] if e.args else None
            retryable = code in (1213, 1205)
            if retryable and i < attempts - 1:
                logger.info("DB retry code=%s attempt=%s/%s", code, i + 1, attempts)
                await asyncio.sleep((0.2 * (2**i)) + random.uniform(0, 0.2))
                continue
            raise


@dataclass
class FetchResult:
    id_: str
    url: str
    status: int | None
    owner_data: str | None
    owner_json_raw: str | None
    gave_up_429: bool
    error_401873: bool
    error: str | None


async def fetch_owner_with_retry(
    session: aiohttp.ClientSession,
    id_: str,
    url: str,
    *,
    http_sem: asyncio.Semaphore,
    max_attempts: int = MAX_ATTEMPTS_429,
) -> FetchResult:
    sem_cm = http_sem if http_sem is not None else contextlib.nullcontext()
    last_status: int | None = None
    last_body: str = ""

    for attempt in range(1, max_attempts + 1):
        if HTTP_PACING_SECONDS:
            await asyncio.sleep(HTTP_PACING_SECONDS)

        async with sem_cm:
            try:
                async with session.get(url, headers=HEADERS) as resp:
                    last_status = resp.status
                    body = await resp.text()
                    last_body = body
                    body_1l = _body_one_line(body, limit=300)

                    try:
                        data = json.loads(body) if body else {}
                    except Exception:
                        data = {}

                    if _has_error_code_401873(data):
                        alma_instr_401873_logger.info(
                            "401873 attempt=%s/%s id=%s url=%s body=%s",
                            attempt,
                            max_attempts,
                            id_,
                            url,
                            body_1l,
                        )
                        return FetchResult(
                            id_=id_,
                            url=url,
                            status=resp.status,
                            owner_data="401873",
                            owner_json_raw=body,
                            gave_up_429=False,
                            error_401873=True,
                            error=None,
                        )

                    if resp.status == 200:
                        owner_data = _extract_owner_names(data)
                        return FetchResult(
                            id_=id_,
                            url=url,
                            status=resp.status,
                            owner_data=owner_data,
                            owner_json_raw=body,
                            gave_up_429=False,
                            error_401873=False,
                            error=None,
                        )

                    if resp.status == 400:
                        logger.warning("Owner fetch 400 id=%s url=%s body=%s", id_, url, body_1l)
                        return FetchResult(
                            id_=id_,
                            url=url,
                            status=resp.status,
                            owner_data=None,
                            owner_json_raw=body,
                            gave_up_429=False,
                            error_401873=False,
                            error="400 Bad Request",
                        )

                    if resp.status == 429:
                        alma_instr_429_logger.info("429 attempt=%s/%s id=%s url=%s", attempt, max_attempts, id_, url)

                        retry_after = _parse_retry_after_seconds(resp)
                        if retry_after is not None and retry_after > 0:
                            await asyncio.sleep(retry_after + random.uniform(0, JITTER_SECONDS))
                        else:
                            await _sleep_backoff_with_jitter(
                                attempt,
                                base_delay=INITIAL_DELAY_SECONDS,
                                max_delay=MAX_DELAY_SECONDS,
                                jitter=JITTER_SECONDS,
                            )
                        continue

                    if resp.status in (500, 502, 503, 504) and attempt < max_attempts:
                        logger.info(
                            "Owner fetch retry status=%s attempt=%s/%s id=%s",
                            resp.status,
                            attempt,
                            max_attempts,
                            id_,
                        )
                        await _sleep_backoff_with_jitter(
                            attempt,
                            base_delay=1.0,
                            max_delay=30.0,
                            jitter=0.5,
                        )
                        continue

                    logger.warning("Owner fetch skip status=%s id=%s url=%s body=%s", resp.status, id_, url, body_1l)
                    return FetchResult(
                        id_=id_,
                        url=url,
                        status=resp.status,
                        owner_data=None,
                        owner_json_raw=body,
                        gave_up_429=False,
                        error_401873=False,
                        error=f"HTTP {resp.status}",
                    )

            except Exception as e:
                if attempt < max_attempts:
                    logger.info("Owner fetch exception retry attempt=%s/%s id=%s err=%s", attempt, max_attempts, id_, e)
                    await asyncio.sleep(0.2 + random.uniform(0, 0.2))
                    continue

                logger.exception("Owner fetch exception gave up id=%s url=%s", id_, url)
                return FetchResult(
                    id_=id_,
                    url=url,
                    status=last_status,
                    owner_data=None,
                    owner_json_raw=last_body or None,
                    gave_up_429=False,
                    error_401873=False,
                    error=str(e),
                )

    logger.warning("Owner fetch gave up after %s attempts (429) id=%s url=%s", max_attempts, id_, url)
    return FetchResult(
        id_=id_,
        url=url,
        status=last_status,
        owner_data=None,
        owner_json_raw=last_body or None,
        gave_up_429=True,
        error_401873=False,
        error="429 max attempts",
    )


async def upsert_instructors_batch(
    pool: aiomysql.Pool,
    rows: list[FetchResult],
    *,
    db_sem: asyncio.Semaphore,
) -> int:
    if not rows:
        return 0

    sql = """
        INSERT INTO api_alma_instructors (id, owner, owner_json_raw)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            owner = VALUES(owner),
            owner_json_raw = VALUES(owner_json_raw)
    """

    sem_cm = db_sem if db_sem is not None else contextlib.nullcontext()

    async with sem_cm:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                params_list = []
                for r in rows:
                    if r.owner_data is None or r.owner_json_raw is None:
                        continue
                    params_list.append((r.id_, r.owner_data, r.owner_json_raw))

                if not params_list:
                    return 0

                try:
                    await cursor.executemany(sql, params_list)
                    await conn.commit()
                    return len(params_list)
                except pymysql.err.OperationalError as e:
                    code = e.args[0] if e.args else None
                    if code in (1213, 1205):
                        logger.info("DB batch retry code=%s size=%s", code, len(params_list))
                        await conn.rollback()
                        saved = 0
                        for p in params_list:
                            await execute_with_retry(cursor, sql, p, attempts=5)
                            saved += 1
                        await conn.commit()
                        return saved
                    raise


async def process_instructors_urls(
    url_list: dict[str, str],
    pool: aiomysql.Pool,
) -> dict[str, Any]:
    http_sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    db_sem = asyncio.Semaphore(DB_CONCURRENCY)

    items = list(url_list.items())
    total = len(items)

    stats: dict[str, Any] = {
        "total": total,
        "http_ok": 0,
        "http_failed": 0,
        "gave_up_429": 0,
        "error_401873": 0,
        "db_saved": 0,
        "started_at": int(time.time()),
        "duration_s": 0,
    }

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(fetch_owner_with_retry(session, id_=id_, url=url, http_sem=http_sem))
            for id_, url in items
        ]

        results: list[FetchResult] = []
        for fut in asyncio.as_completed(tasks):
            r = await fut
            results.append(r)

            if r.owner_data is not None:
                stats["http_ok"] += 1
            else:
                stats["http_failed"] += 1

            if r.gave_up_429:
                stats["gave_up_429"] += 1
            if r.error_401873:
                stats["error_401873"] += 1

        BATCH_SIZE = 200
        for i in range(0, len(results), BATCH_SIZE):
            batch = results[i : i + BATCH_SIZE]
            saved = await upsert_instructors_batch(pool, batch, db_sem=db_sem)
            stats["db_saved"] += saved

    stats["duration_s"] = int(time.time()) - stats["started_at"]
    return stats
