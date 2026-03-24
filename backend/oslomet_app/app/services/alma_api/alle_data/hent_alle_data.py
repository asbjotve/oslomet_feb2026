"""
importer_alle_data_v4_queue_worker.py (v4 - queue/worker, Pattern B)

Queue/worker-versjon av hele import-jobben, tilpasset ønsket ditt om "Mønster B":
- Når producer er ferdig, legges stop-sentinels (None) på køen umiddelbart,
  og vi await-er workers. (Vi er ikke avhengige av id_queue.join() for korrekt stopp.)

Input "year_input":
  - "all" (case-insensitive)
  - "2026"
  - "2026, 2025" (whitespace ok)

Operasjoner:
1) Finn total_record_count -> pages = ceil(total/100)
2) Hent course_id'er med limit=100 og offset += 100, pages ganger
3) Hent full course-json for hver course_id (view=full) med concurrency (= antall workers)
4) insert_to_db(pool, course_json) kjøres inne i workerne

VIKTIG:
- slett_eksisterende_data(pool, year) forventer "all" som eksakt streng (lowercase).
- Denne koden støtter "all" case-insensitive i year_input, men sørger for å kalle
  slett_eksisterende_data(pool, "all") når year=None.

Robusthet:
- Retry/backoff på punkt 3 ved 429.
- (Valgfritt) enkel retry på punkt 1 og 2 også (429/5xx), slik at store jobber ikke stopper
  på midlertidige nett/API-feil.

Merk:
- Pattern B: vi stopper workers ved å putte N sentinels etter at producer er ferdig,
  og så await workerne. Det gir ryddig shutdown uten at workers blir hengende på queue.get().
"""

from __future__ import annotations

import asyncio
import contextlib
from math import ceil
from typing import Any, Dict, List, Optional

import aiohttp

from config.config import settings

from app.services.alma_api.importer_alle_data2 import insert_to_db  # type: ignore
from app.services.alma_api.db_utils import slett_eksisterende_data  # type: ignore


# -----------------------------
# Konfig
# -----------------------------

BASE_URL = "https://api-na.hosted.exlibrisgroup.com/almaws/v1/courses"
PAGE_SIZE = 100

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {settings.ALMA_API_KEY}",
}


# -----------------------------
# Input-normalisering
# -----------------------------

def normalize_years_input(year_input: str) -> List[Optional[str]]:
    """
    Returnerer liste med år:
      - "all" (case-insensitive) => [None]
      - "2026" => ["2026"]
      - "2026, 2025" => ["2026", "2025"]
    """
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


# -----------------------------
# Query-parametre (punkt 1 og 2)
# -----------------------------

def build_list_params(limit: int, offset: int, year: Optional[str]) -> Dict[str, str | int]:
    """
    Lager query-parametre:
      limit, offset, status=ALL, exact_search=false
    + q=year~YYYY hvis year != None.
    """
    params: Dict[str, str | int] = {
        "limit": limit,
        "offset": offset,
        "status": "ALL",
        "exact_search": "false",
    }
    if year is not None:
        params["q"] = f"year~{year}"
    return params


# -----------------------------
# Generisk HTTP GET med retry (for punkt 1 og 2)
# -----------------------------

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
    """
    Liten, generell retry-wrapper for GET som returnerer JSON.

    Hvorfor:
    - Punkt 1 og 2 er ofte "flaky" ved store jobber hvis API/proxy gir 429/5xx.
    - Vi retry'er på typiske "midlertidige" statuser.

    NB:
    - Hvis API en gang i blant returnerer ikke-JSON på feil, kan du fange ContentTypeError her.
      Jeg har holdt den enkel; si fra hvis du vil ha samme mønster som du hadde før (les resp.text()).
    """
    delay = initial_delay_seconds

    for attempt in range(1, max_attempts + 1):
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                return await resp.json()

            if resp.status in retry_statuses:
                # vent og prøv igjen
                await asyncio.sleep(delay + jitter_seconds * (attempt % 2))
                delay *= 2
                continue

            # "Permanent" feil eller noe vi ikke retry'er på
            text = await resp.text()
            raise RuntimeError(f"GET {url} feilet: status={resp.status}, body={text[:500]}")

    raise RuntimeError(f"GET {url} feilet etter {max_attempts} forsøk (params={params})")


# -----------------------------
# Punkt 1: total_record_count + pages
# -----------------------------

async def get_total_record_count(session: aiohttp.ClientSession, year: Optional[str]) -> int:
    """
    Punkt 1:
    GET /courses?limit=1&offset=0&status=ALL&exact_search=false[&q=year~YYYY]
    Leser total_record_count.
    """
    params = build_list_params(limit=1, offset=0, year=year)
    data = await get_json_with_retry(session, BASE_URL, headers=HEADERS, params=params)
    return int(data["total_record_count"])


def compute_pages(total_record_count: int, page_size: int = PAGE_SIZE) -> int:
    """
    pages = ceil(total_record_count / 100)
    """
    if total_record_count <= 0:
        return 0
    return ceil(total_record_count / page_size)


async def get_pages_for_year(session: aiohttp.ClientSession, year: Optional[str]) -> int:
    total = await get_total_record_count(session, year=year)
    return compute_pages(total, page_size=PAGE_SIZE)


# -----------------------------
# Punkt 2: course_id'er
# -----------------------------

async def fetch_course_ids_page(
    session: aiohttp.ClientSession,
    year: Optional[str],
    offset: int,
    limit: int = PAGE_SIZE,
) -> List[str]:
    """
    Henter én side og returnerer course_id'er.
    """
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
    """
    Producer (punkt 2):
    - Regner pages (punkt 1)
    - Itererer sidene og putter course_id i køen
    """
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


# -----------------------------
# Punkt 3: course detail med retry (429)
# -----------------------------

async def fetch_course_detail_with_retry(
    session: aiohttp.ClientSession,
    course_id: str,
    *,
    max_attempts: int = 5,
    initial_delay_seconds: float = 5.0,
    jitter_seconds: float = 0.3,
) -> Optional[Dict[str, Any]]:
    """
    Punkt 3:
      GET /courses/{course_id}?view=full

    Retry:
      - 200 -> JSON
      - 429 -> backoff
      - andre -> None
    """
    url = f"{BASE_URL}/{course_id}"
    params = {"view": "full"}

    delay = initial_delay_seconds
    for attempt in range(1, max_attempts + 1):
        async with session.get(url, headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                return await resp.json()

            if resp.status == 429:
                await asyncio.sleep(delay + (jitter_seconds * (attempt % 2)))
                delay *= 2
                continue

            # For andre feil kan du evt. logge resp.text()
            return None

    return None


# -----------------------------
# Worker: fetch + insert
# -----------------------------

async def fetch_and_insert_worker(
    worker_id: int,
    session: aiohttp.ClientSession,
    pool,
    id_queue: asyncio.Queue[Optional[str]],
    *,
    year: Optional[str],
) -> None:
    """
    Worker:
    - get() course_id
    - None => stopp
    - fetch detail
    - insert_to_db(pool, course_json)
    """
    while True:
        course_id = await id_queue.get()
        try:
            if course_id is None:
                return

            course_json = await fetch_course_detail_with_retry(session, course_id)
            if course_json is None:
                # Ikke stopp workeren; hopp over denne ID'en og fortsett
                # print(f"[year={year}] Worker {worker_id}: Mangler detail for {course_id}")
                continue

            await insert_to_db(pool, course_json)

        finally:
            id_queue.task_done()


# -----------------------------
# Orkestrering per år (Pattern B)
# -----------------------------

async def run_import_for_one_year_queue_worker(
    pool,
    year: Optional[str],
    *,
    concurrency: int = 31,
    id_queue_maxsize: int = 2000,
    polite_sleep_seconds: float = 0.2,
    delete_existing_first: bool = True,
) -> None:
    """
    Pattern B:
    - Start workers
    - Kjør producer til den er ferdig
    - Legg N sentinels (None) på id_queue for å stoppe workers
    - Await workers
    """
    if delete_existing_first:
        # slett_eksisterende_data krever "all" som eksakt lowercase
        if year is None:
            await slett_eksisterende_data(pool, "all")
        else:
            await slett_eksisterende_data(pool, year)

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

        produced: int | None = None

        try:
            # 1) Vent til producer er ferdig (alle course_id'er er nå puttet i køen)
            produced = await producer_task

            # 2) Legg stop-sentinels. Dette sikrer at workers ikke blir hengende i get()
            for _ in range(concurrency):
                await id_queue.put(None)

            # 3) Vent til workers er ferdige.
            # Workers vil:
            # - prosessere alle IDer som ligger foran sentinelene
            # - deretter lese None og returnere
            await asyncio.gather(*workers, return_exceptions=True)

            # Valgfritt:
            # print(f"[year={year}] Produsert IDs: {produced}")

        finally:
            # Hvis producer fortsatt kjører (feil/cancel) -> stopp den
            if not producer_task.done():
                producer_task.cancel()
                with contextlib.suppress(Exception):
                    await producer_task

            # Sørg for at workers får mulighet til å avslutte selv ved feil
            # (put_nowait kan feile hvis køen er full; vi ignorerer i suppress)
            for _ in range(concurrency):
                with contextlib.suppress(Exception):
                    id_queue.put_nowait(None)

            for w in workers:
                if not w.done():
                    w.cancel()

            with contextlib.suppress(Exception):
                await asyncio.gather(*workers, return_exceptions=True)


# -----------------------------
# Offentlig funksjon: year_input (all eller flere år)
# -----------------------------

async def import_alle_data_queue_worker(
    pool,
    year_input: str,
    *,
    concurrency: int = 31,
    id_queue_maxsize: int = 2000,
    polite_sleep_seconds: float = 0.2,
    delete_existing_first: bool = True,
) -> None:
    """
    Kall fra route:
      await import_alle_data_queue_worker(pool, year_input)

    year_input:
      - "all" / "ALL" / ...
      - "2026"
      - "2026, 2025"

    Importen kjøres år for år (sekvensielt).
    """
    years = normalize_years_input(year_input)

    for year in years:
        await run_import_for_one_year_queue_worker(
            pool=pool,
            year=year,
            concurrency=concurrency,
            id_queue_maxsize=id_queue_maxsize,
            polite_sleep_seconds=polite_sleep_seconds,
            delete_existing_first=delete_existing_first,
        )
