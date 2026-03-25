from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, Dict, Optional

import aiohttp
import aiomysql

from app.services.alma_api.helpers import get_nested, prepare_date, safe
from config.config import settings

logger = logging.getLogger(__name__)

# Harmonisert: EU
BASE_URL = "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses"
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {settings.ALMA_API_KEY}",
}

HTTP_PACING_SECONDS = 0.02
RETRY_STATUSES = (429, 500, 502, 503, 504)


def _parse_retry_after_seconds(resp: aiohttp.ClientResponse) -> Optional[float]:
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


async def fetch_course_json(
    session: aiohttp.ClientSession,
    kurs_id: str,
    *,
    max_attempts: int = 8,
    initial_delay_seconds: float = 2.0,
    max_delay_seconds: float = 60.0,
    jitter_seconds: float = 1.0,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/{kurs_id}"
    params = {"view": "full"}

    for attempt in range(1, max_attempts + 1):
        if HTTP_PACING_SECONDS:
            await asyncio.sleep(HTTP_PACING_SECONDS)

        async with session.get(url, headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                return await resp.json()

            body = await resp.text()
            body_one_line = " ".join(body.split())

            if resp.status in RETRY_STATUSES:
                logger.info(
                    "fetch_course_json retry attempt=%s/%s status=%s kurs_id=%s body=%s",
                    attempt,
                    max_attempts,
                    resp.status,
                    kurs_id,
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

            raise RuntimeError(
                f"Alma GET feilet for kurs_id={kurs_id}: status={resp.status} body={body_one_line[:500]}"
            )

    raise RuntimeError(f"Alma GET feilet etter {max_attempts} forsøk for kurs_id={kurs_id}")


async def get_kurs_id_for_pensumliste(pool: aiomysql.Pool, pensumliste_id: str) -> str:
    sql = "SELECT kurs_id FROM api_alma_pensumlister WHERE id = %s LIMIT 1"

    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            await c.execute(sql, (pensumliste_id,))
            row = await c.fetchone()

    if not row or not row[0]:
        raise LookupError(
            f"Fant ikke kurs_id for pensumliste_id={pensumliste_id} i api_alma_pensumlister (finnes den i DB?)"
        )

    return str(row[0])


def find_reading_list(course_json: Dict[str, Any], pensumliste_id: str) -> Optional[Dict[str, Any]]:
    reading_lists = get_nested(course_json, ["reading_lists", "reading_list"], [])
    for rl in reading_lists:
        if safe(rl.get("id")) == str(pensumliste_id):
            return rl
    return None


def _derive_course_year_and_aarsem(course_json: Dict[str, Any]) -> tuple[int, str]:
    raw_year = course_json.get("year")
    digits = "".join(ch for ch in str(raw_year or "") if ch.isdigit())
    c_year = int(digits[:4]) if len(digits) >= 4 else 0
    if c_year < 1900 or c_year > 2100:
        c_year = 0

    term_list = course_json.get("term")
    if isinstance(term_list, list) and len(term_list) > 0 and "value" in term_list[0]:
        c_termvalue = term_list[0]["value"]
    else:
        c_termvalue = ""

    aarsem = f"{c_year}{c_termvalue}"
    return c_year, aarsem


def _extract_pensumliste_fields(
    rl: Dict[str, Any],
    *,
    kurs_id: str,
    course_year: int,
    aarsem: str,
) -> Dict[str, Any]:
    rl_id = safe(rl.get("id"))
    rl_code = safe(rl.get("code"))
    rl_name = safe(rl.get("name"))
    rl_link = safe(get_nested(rl, ["link"]))
    rl_duebackdate = prepare_date(get_nested(rl, ["due_back_date"]))
    rl_status = safe(get_nested(rl, ["status", "value"]))
    rl_syllabus = json.dumps(get_nested(rl, ["syllabus"])) if get_nested(rl, ["syllabus"]) is not None else "{}"
    rl_score = get_nested(rl, ["score"])
    rl_stickerprice = get_nested(rl, ["sticker_price"])
    rl_coveredbylibrary = get_nested(rl, ["covered_by_the_library"])
    rl_visibility = json.dumps(get_nested(rl, ["visibility"])) if get_nested(rl, ["visibility"]) is not None else "{}"
    rl_publishingstatus = (
        json.dumps(get_nested(rl, ["publishingStatus"])) if get_nested(rl, ["publishingStatus"]) is not None else "{}"
    )
    rl_order = get_nested(rl, ["order"])
    rl_notes = json.dumps(get_nested(rl, ["notes"])) if get_nested(rl, ["notes"]) is not None else "[]"
    rl_description = safe(get_nested(rl, ["description"]))
    rl_locked = get_nested(rl, ["locked"])
    rl_lastmodifieddate = prepare_date(get_nested(rl, ["last_modified_date"]))

    rl_owner_url = f"{BASE_URL}/{kurs_id}/reading-lists/{rl_id}/owners"

    return {
        "id": rl_id,
        "kurs_id": kurs_id,
        "code": rl_code,
        "name": rl_name,
        "link": rl_link,
        "due_back_date": rl_duebackdate,
        "status": rl_status,
        "syllabus": rl_syllabus,
        "score": rl_score,
        "sticker_price": rl_stickerprice,
        "covered_by_the_library": rl_coveredbylibrary,
        "visibility": rl_visibility,
        "publishingStatus": rl_publishingstatus,
        "_order": rl_order,
        "notes": rl_notes,
        "description": rl_description,
        "locked": rl_locked,
        "last_modified_date": rl_lastmodifieddate,
        "course_year": course_year,
        "aarsem": aarsem,
        "owner_url": rl_owner_url,
    }


async def upsert_api_alma_pensumliste(pool: aiomysql.Pool, row: Dict[str, Any]) -> None:
    sql = """
    INSERT INTO api_alma_pensumlister (
        id, kurs_id, code, name, link, due_back_date, status, syllabus, score,
        sticker_price, covered_by_the_library,
        visibility, publishingStatus, `_order`, notes, description, locked,
        last_modified_date, course_year, aarsem, owner_url
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        kurs_id=VALUES(kurs_id),
        code=VALUES(code),
        name=VALUES(name),
        link=VALUES(link),
        due_back_date=VALUES(due_back_date),
        status=VALUES(status),
        syllabus=VALUES(syllabus),
        score=VALUES(score),
        sticker_price=VALUES(sticker_price),
        covered_by_the_library=VALUES(covered_by_the_library),
        visibility=VALUES(visibility),
        publishingStatus=VALUES(publishingStatus),
        `_order`=VALUES(`_order`),
        notes=VALUES(notes),
        description=VALUES(description),
        locked=VALUES(locked),
        last_modified_date=VALUES(last_modified_date),
        course_year=VALUES(course_year),
        aarsem=VALUES(aarsem),
        owner_url=VALUES(owner_url)
    """

    params = (
        row["id"],
        row["kurs_id"],
        row["code"],
        row["name"],
        row["link"],
        row["due_back_date"],
        row["status"],
        row["syllabus"],
        row["score"],
        row["sticker_price"],
        row["covered_by_the_library"],
        row["visibility"],
        row["publishingStatus"],
        row["_order"],
        row["notes"],
        row["description"],
        row["locked"],
        row["last_modified_date"],
        row["course_year"],
        row["aarsem"],
        row["owner_url"],
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            try:
                await c.execute(sql, params)
                await conn.commit()
            except Exception:
                await conn.rollback()
                logger.exception("upsert_api_alma_pensumliste feilet for pensumliste_id=%s", row.get("id"))
                raise


async def oppdater_pensumliste(pool: aiomysql.Pool, pensumliste_id: str) -> Dict[str, Any]:
    kurs_id = await get_kurs_id_for_pensumliste(pool, pensumliste_id)

    async with aiohttp.ClientSession() as session:
        course_json = await fetch_course_json(session, kurs_id)

    rl = find_reading_list(course_json, pensumliste_id)
    if rl is None:
        # Tydelig melding: kan være slettet/fjernet i Alma, eller ikke lenger koblet til kurset
        raise LookupError(
            "Pensumlisten ble ikke funnet i Alma-responsen for kurset. "
            f"pensumliste_id={pensumliste_id} kurs_id={kurs_id}. "
            "Den kan være slettet/fjernet i Alma eller ikke lenger knyttet til dette kurset."
        )

    course_year, aarsem = _derive_course_year_and_aarsem(course_json)

    row = _extract_pensumliste_fields(
        rl,
        kurs_id=kurs_id,
        course_year=course_year,
        aarsem=aarsem,
    )

    await upsert_api_alma_pensumliste(pool, row)

    return {
        "status": "ok",
        "pensumliste_id": row["id"],
        "kurs_id": row["kurs_id"],
        "aarsem": row["aarsem"],
        "course_year": row["course_year"],
    }
