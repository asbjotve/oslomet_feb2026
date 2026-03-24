from __future__ import annotations

import asyncio
import contextlib
import logging
from math import ceil
from typing import Any, Dict, List, Optional

import aiohttp
import aiomysql

from config.config import settings
from app.services.alma_api.importer_alle_data2 import insert_to_db
from app.services.alma_api.db_utils import slett_eksisterende_data

logger = logging.getLogger(__name__)

BASE_URL = "https://api-na.hosted.exlibrisgroup.com/almaws/v1/courses"
PAGE_SIZE = 100

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {settings.ALMA_API_KEY}",
}


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


async def get_json_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: Dict[str, str],
    params: Dict[str, str | int] | None = None,
    max_attempts: int = 5,
    initial_delay_seconds: float = 2.0,
    jitter_seconds: float = 0.2,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Dict[str, Any]:
    delay = initial_delay_seconds

    for attempt in range(1, max_attempts + 1):
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                return await resp.json()

            if resp.status in retry_statuses:
                body = await resp.text()
                logger.warning(
                    "GET retry attempt=%s/%s status=%s url=%s params=%s body=%s",
                    attempt,
                    max_attempts,
                    resp.status,
                    url,
                    params,
                    body[:200],
                )
                await asyncio.sleep(delay + jitter_seconds * (attempt % 2))
                delay *= 2
                continue

            body = await resp.text()
            raise RuntimeError(f"GET {url} feilet: status={resp.status}, body={body[:500]}")

    raise RuntimeError(f"GET {url} feilet etter {max_attempts} forsøk (params={params})")


async def get_total_record_count(session: aiohttp.ClientSession, year: Optional[str]) -> int:
    params = build_list_params(limit=1, offset=0, year=year)
    data = await get_json_with_retry(session, BASE_URL, headers=HEADERS, params=params)
    return int(data["total_record_count"])


def compute_pages(total_record_count: int, page_size: int = PAGE_SIZE) -> int:
    if total_record_count <= 0:
        return 0
    return ceil(total_record_count / page_size)


async def get_pages_for_year(session: aiohttp.ClientSession, year: Optional[str]) -> int:
    total = await get_total_record_count(session, year=year)
    return compute_pages(total, page_size=PAGE_SIZE)


async def fetch_course_ids_page(
    session: aiohttp.ClientSession,
    year: Optional[str],
    offset: int,
    limit: int = PAGE_SIZE,
) -> List[str]:
    params = build_list_params(limit=limit, offset=offset, year=year)
    data = await get_json_with_retry(session, BASE_URL, headers=HEADERS, params=params)

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
    polite_sleep_seconds: float = 0.2,
) -> int:
    pages = await get_pages_for_year(session, year=year)
    produced = 0

    for i in range(pages):
        offset = i * PAGE_SIZE
        ids = await fetch_course_ids_page(session, year=year, offset=offset, limit=PAGE_SIZE)

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
    max_attempts: int = 5,
    initial_delay_seconds: float = 5.0,
    jitter_seconds: float = 0.3,
) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/{course_id}"
    params = {"view": "full"}

    delay = initial_delay_seconds
    for attempt in range(1, max_attempts + 1):
        async with session.get(url, headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                return await resp.json()

            if resp.status == 429:
                logger.warning("429 fra Alma attempt=%s/%s course_id=%s", attempt, max_attempts, course_id)
                await asyncio.sleep(delay + (jitter_seconds * (attempt % 2)))
                delay *= 2
                continue

            body = await resp.text()
            logger.warning("Hopper over course_id=%s status=%s body=%s", course_id, resp.status, body[:200])
            return None

    logger.warning("Hopper over course_id=%s etter %s forsøk (429)", course_id, max_attempts)
    return None


async def fetch_and_insert_worker(
    worker_id: int,
    session: aiohttp.ClientSession,
    pool: aiomysql.Pool,
    id_queue: asyncio.Queue[Optional[str]],
    *,
    year: Optional[str],
) -> None:
    while True:
        course_id = await id_queue.get()
        try:
            if course_id is None:
                return

            course_json = await fetch_course_detail_with_retry(session, course_id)
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
    concurrency: int = 31,
    id_queue_maxsize: int = 2000,
    polite_sleep_seconds: float = 0.2,
    delete_existing_first: bool = True,
) -> None:
    if delete_existing_first:
        await slett_eksisterende_data(pool, "all" if year is None else year)

    id_queue: asyncio.Queue[Optional[str]] = asyncio.Queue(maxsize=id_queue_maxsize)

    async with aiohttp.ClientSession() as session:
        workers = [
            asyncio.create_task(
                fetch_and_insert_worker(
                    worker_id=i,
                    session=session,
                    pool=pool,
                    id_queue=id_queue,
                    year=year,
                )
            )
            for i in range(concurrency)
        ]

        producer_task = asyncio.create_task(
            produce_course_ids_to_queue(
                session=session,
                year=year,
                id_queue=id_queue,
                polite_sleep_seconds=polite_sleep_seconds,
            )
        )

        try:
            produced = await producer_task
            logger.info("[year=%s] Produsert course_id-er: %s", year, produced)

            for _ in range(concurrency):
                await id_queue.put(None)

            await asyncio.gather(*workers, return_exceptions=True)

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
    concurrency: int = 31,
    id_queue_maxsize: int = 2000,
    polite_sleep_seconds: float = 0.2,
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
