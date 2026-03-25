from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any, Dict, Iterable

import aiomysql
import pymysql

from config.config import settings
from app.services.alma_api.helpers import (
    analyze_tags,
    analyze_tags_bolk,
    build_json_from_ref_vars,
    extract_numbers,
    generer_import_kommentar,
    get_nested,
    has_isbn_in_content,
    map_academic_department,
    map_bolk_kolonneverdi,
    map_secondary_type,
    prepare_date,
    prepare_year,
    process_unik_bok_id,
    process_unik_utdrag_id,
    process_url,
    safe,
    sammensatt_sideangivelse,
    strip_tags,
    validate_filelink,
)

logger = logging.getLogger(__name__)

# Beholdt for kompatibilitet (noen andre moduler kan importere disse konstantene),
# men denne fila bør ikke stå for env-loading i en FastAPI-app.
API_KEY = settings.ALMA_API_KEY
BASE_URL = "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses"
HEADERS = {"Accept": "application/json", "Authorization": f"apikey {API_KEY}"}

CONCURRENT_REQUESTS = 15
DEBUG_DB_WARNINGS = False

# --- Debug helpers ------------------------------------------------------------

async def _print_db_warnings(c, label: str, ctx: dict[str, Any] | None = None) -> None:
    if not DEBUG_DB_WARNINGS:
        return

    try:
        await c.execute("SHOW WARNINGS")
        warns = await c.fetchall()
        if warns:
            print(f"DB WARNINGS ({label}): ctx={ctx} warns={warns[:10]}", flush=True)
    except Exception as e:
        print(f"FAILED SHOW WARNINGS ({label}): {e} ctx={ctx}", flush=True)


async def execute_with_retry(c, sql: str, params: tuple, attempts: int = 5) -> None:
    """
    Retry for transient MySQL errors under concurrency.
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
                # Low-noise info so you can see that retries happen.
                logger.info("DB retry code=%s attempt=%s/%s", code, i + 1, attempts)

                # Exponential backoff + jitter to avoid synchronized retries.
                await asyncio.sleep((0.2 * (2**i)) + random.uniform(0, 0.2))
                continue
            raise


# --- Main ---------------------------------------------------------------------

async def insert_to_db(pool: aiomysql.Pool, course_json: Dict[str, Any]) -> None:
    """
    Best effort (Alternativ A):
    - Vi forsøker å skrive så mye vi kan for hvert kurs.
    - Enkelt-feil logges og vi fortsetter (samme filosofi som originalen).
    - Vi committer til slutt, siden autocommit=False i pool-configen.
    - Rollback kun ved 'fatal' feil som gjør at vi ikke kan fortsette funksjonen.
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            try:
                # --- Kurs ---
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

                # YEAR: clamp hardt til 4-sifret år (unngå "out of range" på INT-kolonne)
                raw_year = course_json.get("year")
                digits = "".join(ch for ch in str(raw_year or "") if ch.isdigit())
                c_year = int(digits[:4]) if len(digits) >= 4 else 0
                if c_year < 1900 or c_year > 2100:
                    c_year = 0

                # --- MIDLERIDIG DEBUG: logg mistenkelige year ---
                if c_year == 0 and raw_year not in (None, "", 0):
                    print(
                        "SUS YEAR (kurs):",
                        {"course_id": c_id, "raw_year": raw_year, "digits": digits, "c_year": c_year},
                        flush=True,
                    )
                # --- SLUTT DEBUG ---

                c_instructor = json.dumps(course_json.get("instructor")) if course_json.get("instructor") is not None else "[]"
                c_campus = json.dumps(course_json.get("campus")) if course_json.get("campus") is not None else "[]"
                c_searchableids = (
                    json.dumps(course_json.get("searchable_ids")) if course_json.get("searchable_ids") is not None else "[]"
                )
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

                try:
                    await c.execute(
                        """
                        INSERT IGNORE INTO api_alma_kurs (
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
                        """,
                        (
                            c_id,
                            c_code,
                            c_name,
                            c_academicdepartment,
                            c_processingdepartment,
                            c_term,
                            c_status,
                            c_visibility,
                            c_startdate,
                            c_enddate,
                            c_weeklyhours,
                            c_participants,
                            c_year,
                            c_instructor,
                            c_campus,
                            c_searchableids,
                            c_notes,
                            c_createdby,
                            c_createddate,
                            c_lastmodifieddate,
                            c_rolledfrom,
                            c_submitbydate,
                            c_yearterm,
                            c_link,
                            c_fakultet,
                        ),
                    )
                    await _print_db_warnings(c, "api_alma_kurs", {"course_id": c_id, "c_year": c_year, "raw_year": raw_year})
                except Exception:
                    logger.exception("Feil for kurs %s", c_id)

                # --- Pensumlister ---
                reading_lists = get_nested(course_json, ["reading_lists", "reading_list"], [])
                for rl in reading_lists:
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
                    rl_visibility_kobling = get_nested(rl, ["visibility", "value"])
                    rl_publishingstatus = (
                        json.dumps(get_nested(rl, ["publishingStatus"])) if get_nested(rl, ["publishingStatus"]) is not None else "{}"
                    )
                    rl_order = get_nested(rl, ["order"])
                    rl_notes = json.dumps(get_nested(rl, ["notes"])) if get_nested(rl, ["notes"]) is not None else "[]"
                    rl_description = safe(get_nested(rl, ["description"]))
                    rl_locked = get_nested(rl, ["locked"])
                    rl_lastmodifieddate = prepare_date(get_nested(rl, ["last_modified_date"]))
                    rl_aarsem = c_yearterm
                    rl_year = c_year
                    rl_owner_url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses/{c_id}/reading-lists/{rl_id}/owners"

                    try:
                        await execute_with_retry(
                            c,
                            """
                            INSERT IGNORE INTO api_alma_pensumlister (
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
                            """,
                            (
                                rl_id,
                                c_id,
                                rl_code,
                                rl_name,
                                rl_link,
                                rl_duebackdate,
                                rl_status,
                                rl_syllabus,
                                rl_score,
                                rl_stickerprice,
                                rl_coveredbylibrary,
                                rl_visibility,
                                rl_publishingstatus,
                                rl_order,
                                rl_notes,
                                rl_description,
                                rl_locked,
                                rl_lastmodifieddate,
                                rl_year,
                                rl_aarsem,
                                rl_owner_url,
                            ),
                            attempts=5,
                        )
                        await _print_db_warnings(c, "api_alma_pensumlister", {"course_id": c_id, "rl_id": rl_id})
                    except Exception:
                        logger.exception("Feil for pensumliste %s (kurs %s)", rl_id, c_id)

                    # --- Koblingstabell ---
                    try:
                        await execute_with_retry(
                            c,
                            """
                            INSERT IGNORE INTO api_alma_kurs_pensumlister_kobling (
                                kurs_id, pensumliste_id, aarsem, aar, status_pensumliste, term, code, status_pensumliste2
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            """,
                            (c_id, rl_id, c_yearterm, c_year, rl_visibility_kobling, c_termvalue, c_code, rl_status),
                        )
                        await _print_db_warnings(c, "api_alma_kurs_pensumlister_kobling", {"course_id": c_id, "rl_id": rl_id})
                    except Exception:
                        logger.exception("Feil for kobling kurs %s og pensumliste %s", c_id, rl_id)

                    # --- Referanser (citations) ---
                    citations = get_nested(rl, ["citations", "citation"], [])
                    for ref in citations:
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

                        ref_pensumliste_id = rl_id
                        ref_kurs_id = c_id

                        citation_tags_json = get_nested(ref, ["citation_tags"])
                        ref_citation_tags = analyze_tags(citation_tags_json, ref_file_link)
                        ref_citation_tags_bolk = analyze_tags_bolk(citation_tags_json)

                        ref_course_year = c_year
                        ref_aarsem = c_yearterm

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

                        try:
                            await c.execute(
                                """
                                INSERT IGNORE INTO api_alma_referanser (
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
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                                """,
                                (
                                    ref_id,
                                    ref_status,
                                    ref_copyrights_status,
                                    ref_material_type,
                                    ref_leganto_permalink,
                                    ref_file_link,
                                    ref_file_link_filendelse,
                                    ref_public_note,
                                    ref_note,
                                    ref_license_type,
                                    ref_last_modified_date,
                                    ref_title,
                                    ref_aarsem,
                                    ref_author,
                                    ref_publisher,
                                    ref_publication_date,
                                    ref_edition,
                                    ref_isbn,
                                    ref_issn,
                                    ref_mms_id,
                                    ref_additional_person_name,
                                    ref_place_of_publication,
                                    ref_metadata_note,
                                    ref_journal_title,
                                    ref_article_title,
                                    ref_kurs_id,
                                    ref_pensumliste_id,
                                    ref_citation_tags,
                                    ref_year,
                                    ref_issue,
                                    ref_editor,
                                    ref_chapter,
                                    ref_chapter_title,
                                    ref_chapter_author,
                                    ref_pages,
                                    ref_doi,
                                    ref_volume,
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
                                    ref_unik_bok_id,
                                    ref_unik_utdrag_id,
                                    ref_course_year,
                                    ref_endringsurl,
                                    ref_file_validate,
                                    ref_kommentar,
                                    ref_sam_sideangivelse,
                                    ref_secondary_type,
                                    ref_map_secondary_type,
                                    ref_citation_tags_bolk,
                                    ref_bolk_kolonneverdi,
                                    ref_isbnkommentar,
                                ),
                            )
                            await _print_db_warnings(c, "api_alma_referanser", {"course_id": c_id, "rl_id": rl_id, "ref_id": ref_id})
                        except Exception:
                            logger.exception("Feil for referanse %s (pensumliste %s)", ref_id, rl_id)

                # Viktig: commit det som faktisk gikk inn (autocommit=False)
                await conn.commit()

            except Exception:
                # Fatal feil (DB/conn/cursor). Rollback for sikkerhets skyld.
                await conn.rollback()
                logger.exception("Fatal feil i insert_to_db (course id=%s)", course_json.get("id"))
                raise
