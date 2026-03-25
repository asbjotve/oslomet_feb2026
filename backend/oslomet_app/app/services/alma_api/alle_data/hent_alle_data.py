from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import random
from logging.handlers import RotatingFileHandler
from math import ceil
from typing import Any, Dict, List, Optional

import aiohttp
import aiomysql

from app.services.alma_api.db_utils import slett_eksisterende_data
from app.services.alma_api.importer_alle_data2 import insert_to_db
from config.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api-na.hosted.exlibrisgroup.com/almaws/v1/courses"
PAGE_SIZE = 100

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {settings.ALMA_API_KEY}",
}

# ---------------------------- Tuning knobs -----------------------------------
DEFAULT_WORKER_CONCURRENCY = 31

# Max samtidige Alma-kall for course details
HTTP_CONCURRENCY_DETAILS = 25

# Max samtidige Alma-kall for listing/paging
HTTP_CONCURRENCY_LISTING = 2  # 1-3 er typisk bra

# Litt pacing for å unngå bursts (sekunder). 0.0 = av
HTTP_PACING_SECONDS = 0.02
# -----------------------------------------------------------------------------


# ------------------------ Dedicated 429 loggers -------------------------------
LOG_BASE_DIR = "/home/ubuntu/github_oslomet_f2026/backend/oslomet_app/log/oslomet"
DETAIL_429_LOG_PATH = f"{LOG_BASE_DIR}/alma_429.log"
LIST_429_LOG_PATH = f"{LOG_BASE_DIR}/alma_list_429.log"


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


alma429_logger = _make_rotating_file_logger("alma429", DETAIL_429_LOG_PATH, logging.INFO)
alma429_list_logger = _make_rotating_file_logger("alma429.list", LIST_429_LOG_PATH, logging.INFO)
# -----------------------------------------------------------------------------


def normalize_years_input(year_input: str) -> List[Optional[str]]:
    if year_input is None:
        raise ValueError("year_input kan ikke være None")

    raw = year_input.strip()
    if not raw:
        raise ValueError("year_input kan ikke være tom")

    if raw.lower() == "all":
        return [None]

    years = [p.strip() for p in raw.split(",") if p.strip()]
    if not years:
        raise ValueError("Fant ingen år i input")

    for y in years:
        if not y.isdigit():
            raise ValueError(f"Ugyldig år: {y}")

    return years


def build_list_params(limit: int, offset: int, year: Optional[str]) -> Dict[str, str | int]:
    params: Dict[str, str | int] = {
        "limit": limit,
        "offset": offset,
        "status": "ALL",
        "exact_search": "false",
    }
    if year is not None:
        params["q"] = f"year~{year}"
    return params


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


async def get_json_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: Dict[str, str],
    params: Dict[str, str | int] | None = None,
    http_sem: asyncio.Semaphore | None = None,
    retry_logger: logging.Logger | None = None,
    max_attempts: int = 5,
    initial_delay_seconds: float = 4.0,
    max_delay_seconds: float = 120.0,
    jitter_seconds: float = 2.0,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Dict[str, Any]:
    sem_cm = http_sem if http_sem is not None else contextlib.nullcontext()
    retry_logger = retry_logger or logger

    for attempt in range(1, max_attempts + 1):
        if HTTP_PACING_SECONDS:
            await asyncio.sleep(HTTP_PACING_SECONDS)

        async with sem_cm:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()

                body = await resp.text()
                body_one_line = " ".join(body.split())

                if resp.status in retry_statuses:
                    retry_logger.info(
                        "GET retry attempt=%s/%s status=%s url=%s params=%s body=%s",
                        attempt,
                        max_attempts,
                        resp.status,
                        url,
                        params,
                        body_one_line[:200],
                    )

                    retry_after = _parse_retry_after_seconds(resp)
                    if retry_after is not None and retry_after > 0:
                        await asyncio.sleep(retry_after + random.uniform(0, jitter_seconds))
                    else:
                        await _sleep_backoff_with_jitter(
                            attempt,
                            base_delay=initial_delay_seconds,
                            max_delay=max_delay_seconds,
                            jitter=jitter_seconds,
                        )
                    continue

                raise RuntimeError(f"GET {url} feilet: status={resp.status}, body={body_one_line[:500]}")

    raise RuntimeError(f"GET {url} feilet etter {max_attempts} forsøk (params={params})")


async def get_total_record_count(
    session: aiohttp.ClientSession,
    year: Optional[str],
    *,
    http_sem_listing: asyncio.Semaphore | None = None,
) -> int:
    params = build_list_params(limit=1, offset=0, year=year)
    data = await get_json_with_retry(
        session,
        BASE_URL,
        headers=HEADERS,
        params=params,
        http_sem=http_sem_listing,
        retry_logger=alma429_list_logger,
    )
    return int(data["total_record_count"])


def compute_pages(total_record_count: int, page_size: int = PAGE_SIZE) -> int:
    if total_record_count <= 0:
        return 0
    return ceil(total_record_count / page_size)


async def get_pages_for_year(
    session: aiohttp.ClientSession,
    year: Optional[str],
    *,
    http_sem_listing: asyncio.Semaphore | None = None,
) -> int:
    total = await get_total_record_count(session, year=year, http_sem_listing=http_sem_listing)
    return compute_pages(total, page_size=PAGE_SIZE)


async def fetch_course_ids_page(
    session: aiohttp.ClientSession,
    year: Optional[str],
    offset: int,
    *,
    http_sem_listing: asyncio.Semaphore | None = None,
    limit: int = PAGE_SIZE,
) -> List[str]:
    params = build_list_params(limit=limit, offset=offset, year=year)
    data = await get_json_with_retry(
        session,
        BASE_URL,
        headers=HEADERS,
        params=params,
        http_sem=http_sem_listing,
        retry_logger=alma429_list_logger,
    )

    ids: List[str] = []
    for course in (data.get("course") or []):
        cid = course.get("id")
        if cid:
            ids.append(str(cid))
    return ids


async def produce_course_ids_to_queue(
    session: aiohttp.ClientSession,
    year: Optional[str],
    id_queue: asyncio.Queue[Optional[str]],
    *,
    http_sem_listing: asyncio.Semaphore | None = None,
    polite_sleep_seconds: float = 0.5,
) -> int:
    pages = await get_pages_for_year(session, year=year, http_sem_listing=http_sem_listing)
    produced = 0

    for i in range(pages):
        offset = i * PAGE_SIZE
        ids = await fetch_course_ids_page(
            session,
            year=year,
            offset=offset,
            limit=PAGE_SIZE,
            http_sem_listing=http_sem_listing,
        )

        for cid in ids:
            await id_queue.put(cid)
            produced += 1

        if polite_sleep_seconds:
            await asyncio.sleep(polite_sleep_seconds)

    return produced


async def fetch_course_detail_with_retry(
    session: aiohttp.ClientSession,
    course_id: str,
    *,
    http_sem_details: asyncio.Semaphore | None = None,
    max_attempts: int = 10,
    initial_delay_seconds: float = 2.0,
    max_delay_seconds: float = 125.0,
    jitter_seconds: float = 1.0,
) -> tuple[Optional[Dict[str, Any]], bool]:
    """
    Returns: (course_json | None, gave_up_due_to_429: bool)
    """
    url = f"{BASE_URL}/{course_id}"
    params = {"view": "full"}
    sem_cm = http_sem_details if http_sem_details is not None else contextlib.nullcontext()

    for attempt in range(1, max_attempts + 1):
        if HTTP_PACING_SECONDS:
            await asyncio.sleep(HTTP_PACING_SECONDS)

        async with sem_cm:
            async with session.get(url, headers=HEADERS, params=params) as resp:
                if resp.status == 200:
                    return await resp.json(), False

                body = await resp.text()
                body_one_line = " ".join(body.split())

                if resp.status == 429:
                    alma429_logger.info("429 attempt=%s/%s course_id=%s", attempt, max_attempts, course_id)

                    retry_after = _parse_retry_after_seconds(resp)
                    if retry_after is not None and retry_after > 0:
                        await asyncio.sleep(retry_after + random.uniform(0, jitter_seconds))
                    else:
                        await _sleep_backoff_with_jitter(
                            attempt,
                            base_delay=initial_delay_seconds,
                            max_delay=max_delay_seconds,
                            jitter=jitter_seconds,
                        )
                    continue

                logger.warning("Hopper over course_id=%s status=%s body=%s", course_id, resp.status, body_one_line[:200])
                return None, False

    logger.warning("Hopper over course_id=%s etter %s forsøk (429)", course_id, max_attempts)
    return None, True


async def fetch_and_insert_worker(
    worker_id: int,
    session: aiohttp.ClientSession,
    pool: aiomysql.Pool,
    id_queue: asyncio.Queue[Optional[str]],
    *,
    year: Optional[str],
    http_sem_details: asyncio.Semaphore | None = None,
    skipped_429: dict[str, int] | None = None,
    skipped_429_lock: asyncio.Lock | None = None,
) -> None:
    while True:
        course_id = await id_queue.get()
        try:
            if course_id is None:
                return

            course_json, gave_up_429 = await fetch_course_detail_with_retry(
                session,
                course_id,
                http_sem_details=http_sem_details,
            )

            if gave_up_429 and skipped_429 is not None and skipped_429_lock is not None:
                async with skipped_429_lock:
                    skipped_429["count"] += 1

            if course_json is None:
                continue

            try:
                await insert_to_db(pool, course_json)
            except Exception:
                logger.exception("[year=%s] Worker %s: insert_to_db feilet course_id=%s", year, worker_id, course_id)
                continue

        finally:
            id_queue.task_done()


async def run_import_for_one_year_queue_worker(
    pool: aiomysql.Pool,
    year: Optional[str],
    *,
    concurrency: int = 20,
    id_queue_maxsize: int = 2000,
    polite_sleep_seconds: float = 0.5,
    delete_existing_first: bool = True,
) -> None:
    if delete_existing_first:
        await slett_eksisterende_data(pool, "all" if year is None else year)

    id_queue: asyncio.Queue[Optional[str]] = asyncio.Queue(maxsize=id_queue_maxsize)

    skipped_429: dict[str, int] = {"count": 0}
    skipped_429_lock = asyncio.Lock()

    http_sem_details = asyncio.Semaphore(HTTP_CONCURRENCY_DETAILS)
    http_sem_listing = asyncio.Semaphore(HTTP_CONCURRENCY_LISTING)

    async with aiohttp.ClientSession() as session:
        workers = [
            asyncio.create_task(
                fetch_and_insert_worker(
                    worker_id=i,
                    session=session,
                    pool=pool,
                    id_queue=id_queue,
                    year=year,
                    http_sem_details=http_sem_details,
                    skipped_429=skipped_429,
                    skipped_429_lock=skipped_429_lock,
                )
            )
            for i in range(concurrency)
        ]

        producer_task = asyncio.create_task(
            produce_course_ids_to_queue(
                session=session,
                year=year,
                id_queue=id_queue,
                http_sem_listing=http_sem_listing,
                polite_sleep_seconds=polite_sleep_seconds,
            )
        )

        try:
            produced = await producer_task
            logger.info("[year=%s] Produsert course_id-er: %s", year, produced)

            for _ in range(concurrency):
                await id_queue.put(None)

            await asyncio.gather(*workers, return_exceptions=True)

            logger.warning("[year=%s] Skipped courses due to 429: %s", year, skipped_429["count"])

        finally:
            if not producer_task.done():
                producer_task.cancel()
                with contextlib.suppress(Exception):
                    await producer_task

            for _ in range(concurrency):
                with contextlib.suppress(Exception):
                    id_queue.put_nowait(None)

            for w in workers:
                if not w.done():
                    w.cancel()

            with contextlib.suppress(Exception):
                await asyncio.gather(*workers, return_exceptions=True)


async def import_alle_data_queue_worker(
    pool: aiomysql.Pool,
    year_input: str,
    *,
    concurrency: int = DEFAULT_WORKER_CONCURRENCY,
    id_queue_maxsize: int = 2000,
    polite_sleep_seconds: float = 0.5,
    delete_existing_first: bool = True,
) -> None:
    years = normalize_years_input(year_input)

    for year in years:
        logger.info("Starter import: year=%s", year if year is not None else "ALL")
        await run_import_for_one_year_queue_worker(
            pool=pool,
            year=year,
            concurrency=concurrency,
            id_queue_maxsize=id_queue_maxsize,
            polite_sleep_seconds=polite_sleep_seconds,
            delete_existing_first=delete_existing_first,
        )
        logger.info("Ferdig import: year=%s", year if year is not None else "ALL")
