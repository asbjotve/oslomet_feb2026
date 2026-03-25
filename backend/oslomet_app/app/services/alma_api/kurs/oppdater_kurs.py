from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, Dict, Optional

import aiohttp
import aiomysql

from app.services.alma_api.helpers import get_nested, map_academic_department, prepare_date, safe
from config.config import settings

logger = logging.getLogger(__name__)

# Harmonisert: EU (ikke NA)
BASE_URL = "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {settings.ALMA_API_KEY}",
}

# Litt pacing for å unngå bursts (sekunder). 0.0 = av
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
    """
    Hent ett kurs fra Alma (view=full) med retry/backoff ved 429/5xx.
    """
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


def _extract_course_fields(course_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Samme feltbehandling som i importer_alle_data2, men kun for api_alma_kurs.
    """
    c_id = safe(course_json.get("id"))
    c_code = safe(course_json.get("code"))
    c_name = safe(course_json.get("name"))
    c_academicdepartment = safe(get_nested(course_json, ["academic_department", "value"]))
    c_processingdepartment = safe(get_nested(course_json, ["processing_department", "value"]))
    c_term = json.dumps(course_json.get("term")) if course_json.get("term") is not None else "[]"
    c_status = safe(course_json.get("status"))
    c_visibility = safe(course_json.get("visibility"))
    c_startdate = prepare_date(course_json.get("start_date"))
    c_enddate = prepare_date(course_json.get("end_date"))
    c_weeklyhours = safe(course_json.get("weekly_hours"))
    c_participants = safe(course_json.get("participants"))

    # clamp hardt til 4-sifret år (unngå "out of range" på INT-kolonne)
    raw_year = course_json.get("year")
    digits = "".join(ch for ch in str(raw_year or "") if ch.isdigit())
    c_year = int(digits[:4]) if len(digits) >= 4 else 0
    if c_year < 1900 or c_year > 2100:
        c_year = 0

    c_instructor = json.dumps(course_json.get("instructor")) if course_json.get("instructor") is not None else "[]"
    c_campus = json.dumps(course_json.get("campus")) if course_json.get("campus") is not None else "[]"
    c_searchableids = json.dumps(course_json.get("searchable_ids")) if course_json.get("searchable_ids") is not None else "[]"
    c_notes = json.dumps(course_json.get("notes")) if course_json.get("notes") is not None else "[]"
    c_createdby = safe(course_json.get("created_by"))
    c_createddate = prepare_date(course_json.get("created_date"))
    c_lastmodifieddate = prepare_date(course_json.get("last_modified_date"))
    c_rolledfrom = int(course_json.get("rolled_from")) if course_json.get("rolled_from") not in [None, ""] else 0
    c_submitbydate = prepare_date(course_json.get("submit_by_date"))
    c_link = safe(get_nested(course_json, ["link"]))

    term_list = course_json.get("term")
    if isinstance(term_list, list) and len(term_list) > 0 and "value" in term_list[0]:
        c_termvalue = term_list[0]["value"]
    else:
        c_termvalue = ""

    c_yearterm = f"{c_year}{c_termvalue}"
    c_fakultet = map_academic_department(c_academicdepartment)

    return {
        "id": c_id,
        "code": c_code,
        "name": c_name,
        "academic_department": c_academicdepartment,
        "processing_department": c_processingdepartment,
        "term": c_term,
        "status": c_status,
        "visibility": c_visibility,
        "start_date": c_startdate,
        "end_date": c_enddate,
        "weekly_hours": c_weeklyhours,
        "participants": c_participants,
        "year": c_year,
        "instructor": c_instructor,
        "campus": c_campus,
        "searchable_ids": c_searchableids,
        "notes": c_notes,
        "created_by": c_createdby,
        "created_date": c_createddate,
        "last_modified_date": c_lastmodifieddate,
        "rolled_from": c_rolledfrom,
        "submit_by_date": c_submitbydate,
        "aarsem": c_yearterm,
        "link": c_link,
        "fakultet": c_fakultet,
    }


async def upsert_api_alma_kurs(pool: aiomysql.Pool, course_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Oppdater/sett inn KUN api_alma_kurs for ett kurs.
    Krever at api_alma_kurs.id er UNIQUE/PK.
    """
    row = _extract_course_fields(course_json)

    sql = """
    INSERT INTO api_alma_kurs (
        id, code, name, academic_department, processing_department, term, status, visibility,
        start_date, end_date, weekly_hours, participants,
        year, instructor, campus, searchable_ids, notes,
        created_by, created_date, last_modified_date, rolled_from,
        submit_by_date, aarsem, link, fakultet
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        code=VALUES(code),
        name=VALUES(name),
        academic_department=VALUES(academic_department),
        processing_department=VALUES(processing_department),
        term=VALUES(term),
        status=VALUES(status),
        visibility=VALUES(visibility),
        start_date=VALUES(start_date),
        end_date=VALUES(end_date),
        weekly_hours=VALUES(weekly_hours),
        participants=VALUES(participants),
        year=VALUES(year),
        instructor=VALUES(instructor),
        campus=VALUES(campus),
        searchable_ids=VALUES(searchable_ids),
        notes=VALUES(notes),
        created_by=VALUES(created_by),
        created_date=VALUES(created_date),
        last_modified_date=VALUES(last_modified_date),
        rolled_from=VALUES(rolled_from),
        submit_by_date=VALUES(submit_by_date),
        aarsem=VALUES(aarsem),
        link=VALUES(link),
        fakultet=VALUES(fakultet)
    """

    params = (
        row["id"],
        row["code"],
        row["name"],
        row["academic_department"],
        row["processing_department"],
        row["term"],
        row["status"],
        row["visibility"],
        row["start_date"],
        row["end_date"],
        row["weekly_hours"],
        row["participants"],
        row["year"],
        row["instructor"],
        row["campus"],
        row["searchable_ids"],
        row["notes"],
        row["created_by"],
        row["created_date"],
        row["last_modified_date"],
        row["rolled_from"],
        row["submit_by_date"],
        row["aarsem"],
        row["link"],
        row["fakultet"],
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            try:
                await c.execute(sql, params)
                await conn.commit()
            except Exception:
                await conn.rollback()
                logger.exception("upsert_api_alma_kurs feilet for kurs_id=%s", row.get("id"))
                raise

    return row


async def oppdater_kurs(pool: aiomysql.Pool, kurs_id: str) -> Dict[str, Any]:
    """
    Entry-point ruten kan kalle.
    """
    async with aiohttp.ClientSession() as session:
        course_json = await fetch_course_json(session, kurs_id)
        row = await upsert_api_alma_kurs(pool, course_json)

    return {
        "status": "ok",
        "kurs_id": row["id"],
        "aarsem": row["aarsem"],
        "year": row["year"],
    }
