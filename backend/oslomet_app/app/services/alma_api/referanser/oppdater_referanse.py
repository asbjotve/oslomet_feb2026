from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any, Dict, Optional

import aiohttp
import aiomysql

from app.services.alma_api.helpers import (
    analyze_tags,
    analyze_tags_bolk,
    build_json_from_ref_vars,
    generer_import_kommentar,
    get_nested,
    has_isbn_in_content,
    map_bolk_kolonneverdi,
    map_secondary_type,
    prepare_date,
    process_unik_bok_id,
    process_unik_utdrag_id,
    process_url,
    safe,
    sammensatt_sideangivelse,
    strip_tags,
    validate_filelink,
)
from config.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses"
HEADERS = {"Accept": "application/json", "Authorization": f"apikey {settings.ALMA_API_KEY}"}

HTTP_PACING_SECONDS = 0.02
RETRY_STATUSES = (429, 500, 502, 503, 504)


# ----------------------------- HTTP helpers ----------------------------------

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

            raise RuntimeError(f"Alma GET feilet for kurs_id={kurs_id}: status={resp.status} body={body_one_line[:500]}")

    raise RuntimeError(f"Alma GET feilet etter {max_attempts} forsøk for kurs_id={kurs_id}")


# ----------------------------- DB helpers ------------------------------------

async def get_kurs_og_pensumliste_for_referanse(pool: aiomysql.Pool, referanse_id: str) -> tuple[str, str]:
    sql = """
    SELECT kurs_id, pensumliste_id
    FROM api_alma_referanser
    WHERE id = %s
    LIMIT 1
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            await c.execute(sql, (referanse_id,))
            row = await c.fetchone()

    if not row or not row[0] or not row[1]:
        raise LookupError(f"Fant ikke (kurs_id, pensumliste_id) for referanse_id={referanse_id} i api_alma_referanser")

    return str(row[0]), str(row[1])


async def hard_delete_referanse(pool: aiomysql.Pool, referanse_id: str) -> int:
    """
    Returnerer antall slettede rader (0/1).
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            try:
                await c.execute("DELETE FROM api_alma_referanser WHERE id = %s", (referanse_id,))
                await conn.commit()
                return int(c.rowcount or 0)
            except Exception:
                await conn.rollback()
                logger.exception("hard_delete_referanse feilet referanse_id=%s", referanse_id)
                raise


# -------------------------- Alma JSON search ---------------------------------

def find_reading_list(course_json: Dict[str, Any], pensumliste_id: str) -> Optional[Dict[str, Any]]:
    reading_lists = get_nested(course_json, ["reading_lists", "reading_list"], [])
    for rl in reading_lists:
        if safe(rl.get("id")) == str(pensumliste_id):
            return rl
    return None


def find_citation(rl_json: Dict[str, Any], referanse_id: str) -> Optional[Dict[str, Any]]:
    citations = get_nested(rl_json, ["citations", "citation"], [])
    for ref in citations:
        if safe(ref.get("id")) == str(referanse_id):
            return ref
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


# -------------------------- Referanse mapping --------------------------------

def _extract_referanse_row(
    ref: Dict[str, Any],
    *,
    kurs_id: str,
    pensumliste_id: str,
    course_year: int,
    aarsem: str,
) -> Dict[str, Any]:
    ref_id = safe(ref.get("id"))
    ref_status = json.dumps(get_nested(ref, ["status"])) if get_nested(ref, ["status"]) is not None else None
    ref_copyrights_status = get_nested(ref, ["copyrights_status", "value"])
    ref_material_type = get_nested(ref, ["type", "desc"])
    ref_leganto_permalink = get_nested(ref, ["leganto_permalink"])

    file_link_raw = get_nested(ref, ["file_link"])
    file_info = process_url(file_link_raw)
    ref_file_link = file_info["filnavn"]
    ref_file_link_filendelse = file_info["filendelse"] or ""

    ref_public_note = strip_tags(get_nested(ref, ["public_note"]))
    ref_note = json.dumps(get_nested(ref, ["note"])) if get_nested(ref, ["note"]) is not None else None
    ref_license_type = get_nested(ref, ["license_type"])
    ref_last_modified_date = prepare_date(get_nested(ref, ["last_modified_date"]))

    ref_title = get_nested(ref, ["metadata", "title"])
    ref_author = get_nested(ref, ["metadata", "author"])
    ref_publisher = get_nested(ref, ["metadata", "publisher"])
    ref_publication_date = get_nested(ref, ["metadata", "publication_date"])
    ref_edition = get_nested(ref, ["metadata", "edition"])
    ref_isbn = get_nested(ref, ["metadata", "isbn"])
    ref_issn = get_nested(ref, ["metadata", "issn"])
    ref_mms_id = get_nested(ref, ["metadata", "mms_id"])
    ref_additional_person_name = get_nested(ref, ["metadata", "additional_person_name"])
    ref_place_of_publication = get_nested(ref, ["metadata", "place_of_publication"])
    ref_metadata_note = get_nested(ref, ["metadata", "note"])
    ref_journal_title = get_nested(ref, ["metadata", "journal_title"])
    ref_article_title = get_nested(ref, ["metadata", "article_title"])

    citation_tags_json = get_nested(ref, ["citation_tags"])
    ref_citation_tags = analyze_tags(citation_tags_json, ref_file_link)
    ref_citation_tags_bolk = analyze_tags_bolk(citation_tags_json)

    ref_issue = get_nested(ref, ["metadata", "issue"])
    ref_editor = get_nested(ref, ["metadata", "editor"])
    ref_chapter = get_nested(ref, ["metadata", "chapter"])
    ref_chapter_title = get_nested(ref, ["metadata", "chapter_title"])
    ref_chapter_author = get_nested(ref, ["metadata", "chapter_author"])
    ref_pages = get_nested(ref, ["metadata", "pages"])
    ref_doi = get_nested(ref, ["metadata", "doi"])
    ref_volume = get_nested(ref, ["metadata", "volume"])

    def get_page(n: int):
        return get_nested(ref, ["metadata", f"start_page{n}"])

    def get_end_page(n: int):
        return get_nested(ref, ["metadata", f"end_page{n}"])

    ref_start_page = get_nested(ref, ["metadata", "start_page"])
    ref_end_page = get_nested(ref, ["metadata", "end_page"])
    ref_start_page2 = get_page(2)
    ref_end_page2 = get_end_page(2)
    ref_start_page3 = get_page(3)
    ref_end_page3 = get_end_page(3)
    ref_start_page4 = get_page(4)
    ref_end_page4 = get_end_page(4)
    ref_start_page5 = get_page(5)
    ref_end_page5 = get_end_page(5)
    ref_start_page6 = get_page(6)
    ref_end_page6 = get_end_page(6)
    ref_start_page7 = get_page(7)
    ref_end_page7 = get_end_page(7)
    ref_start_page8 = get_page(8)
    ref_end_page8 = get_end_page(8)
    ref_start_page9 = get_page(9)
    ref_end_page9 = get_end_page(9)
    ref_start_page10 = get_page(10)
    ref_end_page10 = get_end_page(10)

    ref_unik_bok_id = process_unik_bok_id(ref_title, ref_publication_date, ref_publisher, ref_id)
    ref_unik_utdrag_id = process_unik_utdrag_id(
        ref_title,
        ref_chapter_title,
        ref_chapter_author,
        ref_chapter,
        ref_public_note,
        ref_publication_date,
    )

    raw_ref_year = get_nested(ref, ["metadata", "year"])
    m = re.search(r"\b(1[4-9]\d{2}|20\d{2}|21\d{2})\b", str(raw_ref_year or ""))
    ref_year = int(m.group(1)) if m else 0

    ref_file_validate = validate_filelink(ref_file_link)
    ref_kommentar = generer_import_kommentar(ref_file_validate, ref_file_link, ref_citation_tags)

    ref_sam_sideangivelse = sammensatt_sideangivelse(
        ref_start_page,
        ref_end_page,
        ref_start_page2,
        ref_end_page2,
        ref_start_page3,
        ref_end_page3,
        ref_start_page4,
        ref_end_page4,
        ref_start_page5,
        ref_end_page5,
        ref_start_page6,
        ref_end_page6,
        ref_start_page7,
        ref_end_page7,
        ref_start_page8,
        ref_end_page8,
        ref_start_page9,
        ref_end_page9,
        ref_start_page10,
        ref_end_page10,
    )

    ref_endringsurl = build_json_from_ref_vars(
        ref_sam_sideangivelse,
        ref_year,
        ref_publication_date,
        ref_public_note,
        ref_chapter_title,
        ref_chapter,
        ref_chapter_author,
    )

    ref_secondary_type = get_nested(ref, ["secondary_type", "desc"])
    ref_map_secondary_type = map_secondary_type(ref_secondary_type)
    ref_isbnkommentar = has_isbn_in_content(ref_note)

    ref_bolk_kolonneverdi = map_bolk_kolonneverdi(
        ref_copyrights_status,
        ref_license_type,
        citation_tags_json,
        ref_file_link,
        ref_isbnkommentar,
    )

    return {
        "id": ref_id,
        "status": ref_status,
        "copyrights_status": ref_copyrights_status,
        "material_type": ref_material_type,
        "leganto_permalink": ref_leganto_permalink,
        "file_link": ref_file_link,
        "file_link_filendelse": ref_file_link_filendelse,
        "public_note": ref_public_note,
        "note": ref_note,
        "license_type": ref_license_type,
        "last_modified_date": ref_last_modified_date,
        "title": ref_title,
        "aarsem": aarsem,
        "author": ref_author,
        "publisher": ref_publisher,
        "publication_date": ref_publication_date,
        "edition": ref_edition,
        "isbn": ref_isbn,
        "issn": ref_issn,
        "mms_id": ref_mms_id,
        "additional_person_name": ref_additional_person_name,
        "place_of_publication": ref_place_of_publication,
        "metadata_note": ref_metadata_note,
        "journal_title": ref_journal_title,
        "article_title": ref_article_title,
        "kurs_id": kurs_id,
        "pensumliste_id": pensumliste_id,
        "citation_tags": ref_citation_tags,
        "year": ref_year,
        "issue": ref_issue,
        "editor": ref_editor,
        "chapter": ref_chapter,
        "chapter_title": ref_chapter_title,
        "chapter_author": ref_chapter_author,
        "pages": ref_pages,
        "doi": ref_doi,
        "volume": ref_volume,
        "start_page": ref_start_page,
        "end_page": ref_end_page,
        "start_page2": ref_start_page2,
        "end_page2": ref_end_page2,
        "start_page3": ref_start_page3,
        "end_page3": ref_end_page3,
        "start_page4": ref_start_page4,
        "end_page4": ref_end_page4,
        "start_page5": ref_start_page5,
        "end_page5": ref_end_page5,
        "start_page6": ref_start_page6,
        "end_page6": ref_end_page6,
        "start_page7": ref_start_page7,
        "end_page7": ref_end_page7,
        "start_page8": ref_start_page8,
        "end_page8": ref_end_page8,
        "start_page9": ref_start_page9,
        "end_page9": ref_end_page9,
        "start_page10": ref_start_page10,
        "end_page10": ref_end_page10,
        "unik_bok_id": ref_unik_bok_id,
        "unik_utdrag_id": ref_unik_utdrag_id,
        "course_year": course_year,
        "referanse_endringssjekk_json": ref_endringsurl,
        "indikator_vaar_fil": ref_file_validate,
        "kommentar": ref_kommentar,
        "sammensatt_sideangivelse": ref_sam_sideangivelse,
        "secondary_type": ref_secondary_type,
        "map_secondary_type": ref_map_secondary_type,
        "bolk_tag": ref_citation_tags_bolk,
        "bolk_rapp_indikator": ref_bolk_kolonneverdi,
        "isbnkommentar_indi": ref_isbnkommentar,
    }


# ----------------------------- UPSERT ----------------------------------------

_UPSERT_SQL_API_ALMA_REFERANSER = """
INSERT INTO api_alma_referanser (
    id, status, copyrights_status, material_type, leganto_permalink, file_link, file_link_filendelse,
    public_note, note, license_type, last_modified_date, title, aarsem, author, publisher, publication_date,
    edition, isbn, issn, mms_id, additional_person_name, place_of_publication, metadata_note, journal_title,
    article_title, kurs_id, pensumliste_id, citation_tags, year, issue, editor, chapter, chapter_title, chapter_author,
    pages, doi, volume, start_page, end_page, start_page2, end_page2, start_page3, end_page3,
    start_page4, end_page4, start_page5, end_page5, start_page6, end_page6,
    start_page7, end_page7, start_page8, end_page8, start_page9, end_page9,
    start_page10, end_page10, unik_bok_id, unik_utdrag_id, course_year, referanse_endringssjekk_json, indikator_vaar_fil,
    kommentar, sammensatt_sideangivelse, secondary_type, map_secondary_type, bolk_tag, bolk_rapp_indikator, isbnkommentar_indi
) VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON DUPLICATE KEY UPDATE
    status=VALUES(status),
    copyrights_status=VALUES(copyrights_status),
    material_type=VALUES(material_type),
    leganto_permalink=VALUES(leganto_permalink),
    file_link=VALUES(file_link),
    file_link_filendelse=VALUES(file_link_filendelse),
    public_note=VALUES(public_note),
    note=VALUES(note),
    license_type=VALUES(license_type),
    last_modified_date=VALUES(last_modified_date),
    title=VALUES(title),
    aarsem=VALUES(aarsem),
    author=VALUES(author),
    publisher=VALUES(publisher),
    publication_date=VALUES(publication_date),
    edition=VALUES(edition),
    isbn=VALUES(isbn),
    issn=VALUES(issn),
    mms_id=VALUES(mms_id),
    additional_person_name=VALUES(additional_person_name),
    place_of_publication=VALUES(place_of_publication),
    metadata_note=VALUES(metadata_note),
    journal_title=VALUES(journal_title),
    article_title=VALUES(article_title),
    kurs_id=VALUES(kurs_id),
    pensumliste_id=VALUES(pensumliste_id),
    citation_tags=VALUES(citation_tags),
    year=VALUES(year),
    issue=VALUES(issue),
    editor=VALUES(editor),
    chapter=VALUES(chapter),
    chapter_title=VALUES(chapter_title),
    chapter_author=VALUES(chapter_author),
    pages=VALUES(pages),
    doi=VALUES(doi),
    volume=VALUES(volume),
    start_page=VALUES(start_page),
    end_page=VALUES(end_page),
    start_page2=VALUES(start_page2),
    end_page2=VALUES(end_page2),
    start_page3=VALUES(start_page3),
    end_page3=VALUES(end_page3),
    start_page4=VALUES(start_page4),
    end_page4=VALUES(end_page4),
    start_page5=VALUES(start_page5),
    end_page5=VALUES(end_page5),
    start_page6=VALUES(start_page6),
    end_page6=VALUES(end_page6),
    start_page7=VALUES(start_page7),
    end_page7=VALUES(end_page7),
    start_page8=VALUES(start_page8),
    end_page8=VALUES(end_page8),
    start_page9=VALUES(start_page9),
    end_page9=VALUES(end_page9),
    start_page10=VALUES(start_page10),
    end_page10=VALUES(end_page10),
    unik_bok_id=VALUES(unik_bok_id),
    unik_utdrag_id=VALUES(unik_utdrag_id),
    course_year=VALUES(course_year),
    referanse_endringssjekk_json=VALUES(referanse_endringssjekk_json),
    indikator_vaar_fil=VALUES(indikator_vaar_fil),
    kommentar=VALUES(kommentar),
    sammensatt_sideangivelse=VALUES(sammensatt_sideangivelse),
    secondary_type=VALUES(secondary_type),
    map_secondary_type=VALUES(map_secondary_type),
    bolk_tag=VALUES(bolk_tag),
    bolk_rapp_indikator=VALUES(bolk_rapp_indikator),
    isbnkommentar_indi=VALUES(isbnkommentar_indi)
"""


def _upsert_params_from_row(r: Dict[str, Any]) -> tuple:
    return (
        r["id"],
        r["status"],
        r["copyrights_status"],
        r["material_type"],
        r["leganto_permalink"],
        r["file_link"],
        r["file_link_filendelse"],
        r["public_note"],
        r["note"],
        r["license_type"],
        r["last_modified_date"],
        r["title"],
        r["aarsem"],
        r["author"],
        r["publisher"],
        r["publication_date"],
        r["edition"],
        r["isbn"],
        r["issn"],
        r["mms_id"],
        r["additional_person_name"],
        r["place_of_publication"],
        r["metadata_note"],
        r["journal_title"],
        r["article_title"],
        r["kurs_id"],
        r["pensumliste_id"],
        r["citation_tags"],
        r["year"],
        r["issue"],
        r["editor"],
        r["chapter"],
        r["chapter_title"],
        r["chapter_author"],
        r["pages"],
        r["doi"],
        r["volume"],
        r["start_page"],
        r["end_page"],
        r["start_page2"],
        r["end_page2"],
        r["start_page3"],
        r["end_page3"],
        r["start_page4"],
        r["end_page4"],
        r["start_page5"],
        r["end_page5"],
        r["start_page6"],
        r["end_page6"],
        r["start_page7"],
        r["end_page7"],
        r["start_page8"],
        r["end_page8"],
        r["start_page9"],
        r["end_page9"],
        r["start_page10"],
        r["end_page10"],
        r["unik_bok_id"],
        r["unik_utdrag_id"],
        r["course_year"],
        r["referanse_endringssjekk_json"],
        r["indikator_vaar_fil"],
        r["kommentar"],
        r["sammensatt_sideangivelse"],
        r["secondary_type"],
        r["map_secondary_type"],
        r["bolk_tag"],
        r["bolk_rapp_indikator"],
        r["isbnkommentar_indi"],
    )


# ------------------------------ Main -----------------------------------------

async def oppdater_referanse(pool: aiomysql.Pool, referanse_id: str) -> Dict[str, Any]:
    """
    Default: Hvis referansen ikke finnes i Alma lenger -> hard-delete i DB og returner status=deleted.
    """
    kurs_id, pensumliste_id = await get_kurs_og_pensumliste_for_referanse(pool, referanse_id)

    async with aiohttp.ClientSession() as session:
        course_json = await fetch_course_json(session, kurs_id)

    rl = find_reading_list(course_json, pensumliste_id)
    if rl is None:
        # Hvis pensumlisten er borte i Alma, er referansen definitivt ikke lenger gyldig.
        deleted = await hard_delete_referanse(pool, referanse_id)
        return {
            "status": "deleted",
            "referanse_id": str(referanse_id),
            "reason": "Pensumlisten ble ikke funnet i Alma-responsen (antatt fjernet i Alma).",
            "db_deleted_rows": deleted,
        }

    ref = get_nested(rl, ["citations", "citation"], []) or []
    # Finn referansen i Alma
    found = None
    for r in ref:
        if safe(r.get("id")) == str(referanse_id):
            found = r
            break

    if found is None:
        deleted = await hard_delete_referanse(pool, referanse_id)
        return {
            "status": "deleted",
            "referanse_id": str(referanse_id),
            "reason": "Referansen ble ikke funnet i Alma (antatt slettet/fjernet i Alma).",
            "db_deleted_rows": deleted,
        }

    course_year, aarsem = _derive_course_year_and_aarsem(course_json)
    row = _extract_referanse_row(
        found,
        kurs_id=kurs_id,
        pensumliste_id=pensumliste_id,
        course_year=course_year,
        aarsem=aarsem,
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            try:
                await c.execute(_UPSERT_SQL_API_ALMA_REFERANSER, _upsert_params_from_row(row))
                await conn.commit()
            except Exception:
                await conn.rollback()
                logger.exception("Upsert feilet for referanse_id=%s", referanse_id)
                raise

    return {
        "status": "ok",
        "referanse_id": row["id"],
        "pensumliste_id": row["pensumliste_id"],
        "kurs_id": row["kurs_id"],
        "aarsem": row["aarsem"],
        "course_year": row["course_year"],
    }
