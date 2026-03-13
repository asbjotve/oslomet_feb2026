from config.config import settings

# Kopi for bruk i enkeltkurs-endepunkt
async def fetch_course_detail_single(session, course_id):
    url = f"{BASE_URL}/{course_id}?view=full"
    delay = 5.0
    for attempt in range(5):
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 429:
                print(f"Kurs {course_id} ga status 429 (rate limit), venter {delay} sekunder")
                await asyncio.sleep(delay + random.uniform(0, 0.3))
                delay *= 2
            else:
                if attempt == 4:
                    print(f"Kurs {course_id} ga status {resp.status}")
                await asyncio.sleep(0.2)
    return None

async def insert_single_course_to_db(pool, course_json):
    async with pool.acquire() as conn:
        async with conn.cursor() as c:
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
            c_year = safe(prepare_year(course_json.get("year")), 0)
            c_instructor = json.dumps(course_json.get("instructor")) if course_json.get("instructor") is not None else "[]"
            c_campus = json.dumps(course_json.get("campus")) if course_json.get("campus") is not None else "[]"
            c_searchableids = json.dumps(course_json.get("searchable_ids")) if course_json.get("searchable_ids") is not None else "[]"
            c_notes = json.dumps(course_json.get("notes")) if course_json.get("notes") is not None else "[]"
            c_createdby = safe(course_json.get("created_by"))
            c_createddate = prepare_date(course_json.get("created_date"))
            c_lastmodifieddate = prepare_date(course_json.get("last_modified_date"))
            c_rolledfrom = int(course_json.get("rolled_from")) if course_json.get("rolled_from") not in [None, ""] else 0
            c_submitbydate = prepare_date(course_json.get("submit_by_date"))
            c_link = safe(get_nested(course_json, ['link']))
            term_list = course_json.get("term")
            if isinstance(term_list, list) and len(term_list) > 0 and "value" in term_list[0]:
                c_termvalue = term_list[0]["value"]
            else:
                c_termvalue = ""
            c_yearterm = f"{c_year}{c_termvalue}"
            if isinstance(term_list, list) and len(term_list) > 1:
                c_term_has_multiple = 1
            else:
                c_term_has_multiple = 0
            c_fakultet = map_academic_department(c_academicdepartment)

            try:
                await c.execute("""
INSERT INTO api_alma_kurs (
    id, code, name, academic_department, processing_department, term, status, visibility, start_date, end_date, weekly_hours, participants,
    year, instructor, campus, searchable_ids, notes, created_by, created_date, last_modified_date, rolled_from,
    submit_by_date, aarsem, link, fakultet
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON DUPLICATE KEY UPDATE
	id = VALUES(id),
	code = VALUES(code),
	name = VALUES(name),
	academic_department = VALUES(academic_department),
	processing_department = VALUES(processing_department),
	term = VALUES(term),
	status = VALUES(status),
	visibility = VALUES(visibility),
	start_date = VALUES(start_date),
	end_date = VALUES(end_date),
	weekly_hours = VALUES(weekly_hours),
	participants = VALUES(participants),
	year = VALUES(year),
	instructor = VALUES(instructor),
	campus = VALUES(campus),
	searchable_ids = VALUES(searchable_ids),
	notes = notesVALUES(notes),
	created_by = VALUES(created_by),
	created_date = VALUES(created_date),
	last_modified_date = VALUES(last_modified_date),
	rolled_from = VALUES(rolled_from),
	submit_by_date = VALUES(submit_by_date),
	aarsem = VALUES(aarsem),
	link = VALUES(link),
	fakultet = VALUES(fakultet)
""", (
    c_id, c_code, c_name, c_academicdepartment, c_processingdepartment, c_term, c_status, c_visibility,
    c_startdate, c_enddate, c_weeklyhours, c_participants, c_year, c_instructor, c_campus, c_searchableids, c_notes,
    c_createdby, c_createddate, c_lastmodifieddate, c_rolledfrom, c_submitbydate, c_yearterm, c_link, c_fakultet
))
            except Exception as e:
                print(f"Feil for kurs {c_id}: {e}")

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
                rl_visibility_kobling = get_nested(rl, ['visibility', 'value'])
                rl_publishingstatus = json.dumps(get_nested(rl, ["publishingStatus"])) if get_nested(rl, ["publishingStatus"]) is not None else "{}"
                rl_order = get_nested(rl, ["order"])
                rl_notes = json.dumps(get_nested(rl, ["notes"])) if get_nested(rl, ["notes"]) is not None else "[]"
                rl_description = safe(get_nested(rl, ["description"]))
                rl_locked = get_nested(rl, ["locked"])
                rl_lastmodifieddate = prepare_date(get_nested(rl, ["last_modified_date"]))
                rl_aarsem = c_yearterm
                rl_year = c_year
                rl_owner_url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses/{c_id}/reading-lists/{rl_id}/owners"

                try:
                    await c.execute("""
INSERT INTO api_alma_pensumlister (
    id, kurs_id, code, name, link, due_back_date, status, syllabus, score, sticker_price, covered_by_the_library,
    visibility, publishingStatus, `_order`, notes, description, locked, last_modified_date, course_year, aarsem, owner_url
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON DUPLICATE KEY UPDATE
    kurs_id               = VALUES(kurs_id),
    code                  = VALUES(code),
    name                  = VALUES(name),
    link                  = VALUES(link),
    due_back_date         = VALUES(due_back_date),
    status                = VALUES(status),
    syllabus              = VALUES(syllabus),
    score                 = VALUES(score),
    sticker_price         = VALUES(sticker_price),
    covered_by_the_library= VALUES(covered_by_the_library),
    visibility            = VALUES(visibility),
    publishingStatus      = VALUES(publishingStatus),
    `_order`              = VALUES(`_order`),
    notes                 = VALUES(notes),
    description           = VALUES(description),
    locked                = VALUES(locked),
    last_modified_date    = VALUES(last_modified_date),
    course_year           = VALUES(course_year),
    aarsem                = VALUES(aarsem),
    owner_url             = VALUES(owner_url)
""", (
    rl_id, c_id, rl_code, rl_name, rl_link, rl_duebackdate, rl_status, rl_syllabus,
    rl_score, rl_stickerprice, rl_coveredbylibrary, rl_visibility, rl_publishingstatus,
    rl_order, rl_notes, rl_description, rl_locked, rl_lastmodifieddate, rl_year, rl_aarsem, rl_owner_url
))
                except Exception as e:
                    print(f"Feil for pensumliste {rl_id} (kurs {c_id}): {e}")

                # --- Koblingstabell ---
                try:
                    await c.execute("""
                        INSERT IGNORE INTO api_alma_kurs_pensumlister_kobling (
                            kurs_id, pensumliste_id, aarsem, aar, status_pensumliste, term, code, status_pensumliste2
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        c_id, rl_id, c_yearterm, c_year, rl_visibility_kobling, c_termvalue, c_code, rl_status
                    ))
                except Exception as e:
                    print(f"Feil for kobling kurs {c_id} og pensumliste {rl_id}: {e}")

                # --- Referanser (citations) ---
                citations = get_nested(rl, ["citations", "citation"], [])
                for ref in citations:
                    ref_id = safe(ref.get("id"))
                    ref_status = json.dumps(get_nested(ref, ["status"])) if get_nested(ref, ["status"]) is not None else None
                    ref_copyrights_status = json.dumps(get_nested(ref, ["copyrights_status"])) if get_nested(ref, ["copyrights_status"]) is not None else None
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
                    def get_page(n): return get_nested(ref, ["metadata", f"start_page{n}"])
                    def get_end_page(n): return get_nested(ref, ["metadata", f"end_page{n}"])
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
                    ref_unik_utdrag_id = process_unik_utdrag_id(ref_title, ref_chapter_title, ref_chapter_author, ref_chapter, ref_public_note, ref_publication_date)
                    ref_year = extract_numbers(get_nested(ref, ["metadata", "year"]))
                    ref_file_validate = validate_filelink(ref_file_link)
                    ref_kommentar = generer_import_kommentar(ref_file_validate, ref_file_link, ref_citation_tags)
                    ref_sam_sideangivelse = sammensatt_sideangivelse(
                        ref_start_page, ref_end_page,
                        ref_start_page2, ref_end_page2,
                        ref_start_page3, ref_end_page3,
                        ref_start_page4, ref_end_page4,
                        ref_start_page5, ref_end_page5,
                        ref_start_page6, ref_end_page6,
                        ref_start_page7, ref_end_page7,
                        ref_start_page8, ref_end_page8,
                        ref_start_page9, ref_end_page9,
                        ref_start_page10, ref_end_page10
                    )
                    ref_endringsurl = build_json_from_ref_vars(
                        ref_sam_sideangivelse,
                        ref_year, ref_publication_date, ref_public_note,
                        ref_chapter_title, ref_chapter, ref_chapter_author
                    )
                    ref_secondary_type = get_nested(ref, ["secondary_type", "desc"])
                    ref_map_secondary_type = map_secondary_type(ref_secondary_type)
                    bolk_kolonneverdi = map_bolk_kolonneverdi(
                        ref_copyrights_status,
                        ref_license_type,
                        ref_citation_tags,
                        ref_file_link
                    )

                    try:
                        await c.execute("""
INSERT IGNORE INTO api_alma_referanser (
    id, status, copyrights_status, material_type, leganto_permalink, file_link, file_link_filendelse,
    public_note, note, license_type, last_modified_date, title, aarsem, author, publisher, publication_date,
    edition, isbn, issn, mms_id, additional_person_name, place_of_publication, metadata_note, journal_title,
    article_title, kurs_id, pensumliste_id, citation_tags, year, issue, editor, chapter, chapter_title, chapter_author,
    pages, doi, volume, start_page, end_page, start_page2, end_page2, start_page3, end_page3,
    start_page4, end_page4, start_page5, end_page5, start_page6, end_page6,
    start_page7, end_page7, start_page8, end_page8, start_page9, end_page9,
    start_page10, end_page10, unik_bok_id, unik_utdrag_id, course_year, referanse_endringssjekk_json, indikator_vaar_fil,
    kommentar, sammensatt_sideangivelse, secondary_type, map_secondary_type
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
""", (
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
    ref_map_secondary_type
))
                    except Exception as e:
                        print(f"Feil for referanse {ref_id} (pensumliste {rl_id}): {e}")

import os
import json
import random
import asyncio
import aiohttp
import aiomysql
from math import ceil
from pathlib import Path
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from app.services.hent_kursdata.helpers import (
    analyze_tags, safe, get_nested, prepare_date, prepare_year, process_url,
    process_unik_bok_id, process_unik_utdrag_id, extract_numbers, build_json_from_ref_vars,
    validate_filelink, generer_import_kommentar, map_academic_department, sammensatt_sideangivelse, 
    map_secondary_type, strip_tags, analyze_tags_bolk, map_bolk_kolonneverdi, has_isbn_in_content
)
from app.services.hent_kursdata.db_utils import slett_eksisterende_data

import warnings
warnings.simplefilter("always")
import logging
logging.basicConfig(filename="python_warnings.log", level=logging.WARNING)
def log_warning(message, category, filename, lineno, file=None, line=None):
    logging.warning(f"{filename}:{lineno}: {category.__name__}: {message}")
warnings.showwarning = log_warning

# Last inn miljøvariabler
load_dotenv(dotenv_path=".env.oslomet")

API_KEY = settings.ALMA_API_KEY #or "l8xx9c14d664ab9c41c190731eff73df093f"
BASE_URL = "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses"
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"apikey {API_KEY}"
}

CONCURRENT_REQUESTS = 31

async def import_alle_data(pool, year):
    await slett_eksisterende_data(pool, year)


    import aiohttp
    async def get_total_count(session, year=None):
        params = {"limit": 1, "offset": 0, "status": "ALL", "exact_search": "false"}
        if year and year != "all":
            params["q"] = f"year~{year}"
        async with session.get(BASE_URL, headers=HEADERS, params=params) as resp:
            try:
                data = await resp.json()
                return data["total_record_count"]
            except aiohttp.ContentTypeError:
                text = await resp.text()
                print(f"API-feil (status {resp.status}): {text}")
                raise Exception(f"Alma API-feil: {resp.status} {text}")

    async def get_course_ids(session, year=None):
        total = await get_total_count(session, year)
        pages = ceil(total / 100)
        ids = []
        for i in tqdm(range(pages), desc="Henter kurs-IDer", disable=True):
            params = {"limit": 100, "offset": i * 100, "status": "ALL", "exact_search": "false"}
            if year and year != "all":
                params["q"] = f"year~{year}"
            async with session.get(BASE_URL, headers=HEADERS, params=params) as resp:
                data = await resp.json()
                for course in data.get("course", []):
                    if "id" in course:
                        ids.append(course["id"])
            await asyncio.sleep(0.2)
        return ids

    async def fetch_course_detail(session, course_id):
        url = f"{BASE_URL}/{course_id}?view=full"
        delay = 5.0
        for attempt in range(5):
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    print(f"Kurs {course_id} ga status 429 (rate limit), venter {delay} sekunder")
                    await asyncio.sleep(delay + random.uniform(0, 0.3))
                    delay *= 2
                else:
                    if attempt == 4:
                        print(f"Kurs {course_id} ga status {resp.status}")
                    await asyncio.sleep(0.2)
        return None

    async def insert_to_db(pool, course_json):
        async with pool.acquire() as conn:
            async with conn.cursor() as c:
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
                c_year = safe(prepare_year(course_json.get("year")), 0)
                c_instructor = json.dumps(course_json.get("instructor")) if course_json.get("instructor") is not None else "[]"
                c_campus = json.dumps(course_json.get("campus")) if course_json.get("campus") is not None else "[]"
                c_searchableids = json.dumps(course_json.get("searchable_ids")) if course_json.get("searchable_ids") is not None else "[]"
                c_notes = json.dumps(course_json.get("notes")) if course_json.get("notes") is not None else "[]"
                c_createdby = safe(course_json.get("created_by"))
                c_createddate = prepare_date(course_json.get("created_date"))
                c_lastmodifieddate = prepare_date(course_json.get("last_modified_date"))
                c_rolledfrom = int(course_json.get("rolled_from")) if course_json.get("rolled_from") not in [None, ""] else 0
                c_submitbydate = prepare_date(course_json.get("submit_by_date"))
                c_link = safe(get_nested(course_json, ['link']))
                term_list = course_json.get("term")
                if isinstance(term_list, list) and len(term_list) > 0 and "value" in term_list[0]:
                    c_termvalue = term_list[0]["value"]
                else:
                    c_termvalue = ""
                c_yearterm = f"{c_year}{c_termvalue}"
                if isinstance(term_list, list) and len(term_list) > 1:
                    c_term_has_multiple = 1
                else:
                    c_term_has_multiple = 0
                c_fakultet = map_academic_department(c_academicdepartment)

                try:
                    await c.execute("""
    INSERT IGNORE INTO api_alma_kurs (
        id, code, name, academic_department, processing_department, term, status, visibility, start_date, end_date, weekly_hours, participants,
        year, instructor, campus, searchable_ids, notes, created_by, created_date, last_modified_date, rolled_from,
        submit_by_date, aarsem, link, fakultet
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """, (
        c_id, c_code, c_name, c_academicdepartment, c_processingdepartment, c_term, c_status, c_visibility,
        c_startdate, c_enddate, c_weeklyhours, c_participants, c_year, c_instructor, c_campus, c_searchableids, c_notes,
        c_createdby, c_createddate, c_lastmodifieddate, c_rolledfrom, c_submitbydate, c_yearterm, c_link, c_fakultet
    ))
                except Exception as e:
                    print(f"Feil for kurs {c_id}: {e}")

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
                    rl_visibility_kobling = get_nested(rl, ['visibility', 'value'])
                    rl_publishingstatus = json.dumps(get_nested(rl, ["publishingStatus"])) if get_nested(rl, ["publishingStatus"]) is not None else "{}"
                    rl_order = get_nested(rl, ["order"])
                    rl_notes = json.dumps(get_nested(rl, ["notes"])) if get_nested(rl, ["notes"]) is not None else "[]"
                    rl_description = safe(get_nested(rl, ["description"]))
                    rl_locked = get_nested(rl, ["locked"])
                    rl_lastmodifieddate = prepare_date(get_nested(rl, ["last_modified_date"]))
                    rl_aarsem = c_yearterm
                    rl_year = c_year
                    rl_owner_url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/courses/{c_id}/reading-lists/{rl_id}/owners"

                    try:
                        await c.execute("""
    INSERT IGNORE INTO api_alma_pensumlister (
        id, kurs_id, code, name, link, due_back_date, status, syllabus, score, sticker_price, covered_by_the_library,
        visibility, publishingStatus, `_order`, notes, description, locked, last_modified_date, course_year, aarsem, owner_url
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """, (
        rl_id, c_id, rl_code, rl_name, rl_link, rl_duebackdate, rl_status, rl_syllabus,
        rl_score, rl_stickerprice, rl_coveredbylibrary, rl_visibility, rl_publishingstatus,
        rl_order, rl_notes, rl_description, rl_locked, rl_lastmodifieddate, rl_year, rl_aarsem, rl_owner_url
    ))
                    except Exception as e:
                        print(f"Feil for pensumliste {rl_id} (kurs {c_id}): {e}")

                    # --- Koblingstabell ---
                    try:
                        await c.execute("""
                            INSERT IGNORE INTO api_alma_kurs_pensumlister_kobling (
                                kurs_id, pensumliste_id, aarsem, aar, status_pensumliste, term, code, status_pensumliste2
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            c_id, rl_id, c_yearterm, c_year, rl_visibility_kobling, c_termvalue, c_code, rl_status
                        ))
                    except Exception as e:
                        print(f"Feil for kobling kurs {c_id} og pensumliste {rl_id}: {e}")

                    # --- Referanser (citations) ---
                    citations = get_nested(rl, ["citations", "citation"], [])
                    for ref in citations:
                        ref_id = safe(ref.get("id"))
                        ref_status = json.dumps(get_nested(ref, ["status"])) if get_nested(ref, ["status"]) is not None else None
                        ref_copyrights_status = get_nested(ref, ["copyrights_status", "value"])
                        ref_copyrights_s_old = json.dumps(get_nested(ref, ["copyrights_status"])) if get_nested(ref, ["copyrights_status"]) is not None else None
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
                        def get_page(n): return get_nested(ref, ["metadata", f"start_page{n}"])
                        def get_end_page(n): return get_nested(ref, ["metadata", f"end_page{n}"])
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
                        ref_unik_utdrag_id = process_unik_utdrag_id(ref_title, ref_chapter_title, ref_chapter_author, ref_chapter, ref_public_note, ref_publication_date)
                        ref_year = extract_numbers(get_nested(ref, ["metadata", "year"]))
                        ref_file_validate = validate_filelink(ref_file_link)
                        ref_kommentar = generer_import_kommentar(ref_file_validate, ref_file_link, ref_citation_tags)
                        ref_sam_sideangivelse = sammensatt_sideangivelse(
                            ref_start_page, ref_end_page,
                            ref_start_page2, ref_end_page2,
                            ref_start_page3, ref_end_page3,
                            ref_start_page4, ref_end_page4,
                            ref_start_page5, ref_end_page5,
                            ref_start_page6, ref_end_page6,
                            ref_start_page7, ref_end_page7,
                            ref_start_page8, ref_end_page8,
                            ref_start_page9, ref_end_page9,
                            ref_start_page10, ref_end_page10
                        )
                        ref_endringsurl = build_json_from_ref_vars(
                            ref_sam_sideangivelse,
                            ref_year, ref_publication_date, ref_public_note,
                            ref_chapter_title, ref_chapter, ref_chapter_author
                        )
                        ref_secondary_type = get_nested(ref, ["secondary_type", "desc"])
                        ref_map_secondary_type = map_secondary_type(ref_secondary_type)
                        ref_isbnkommentar = has_isbn_in_content(ref_note)
                        
                        print("DEBUG: ", ref_id, ref_copyrights_status, ref_license_type, ref_citation_tags, ref_file_link)
                        print("DEBUG analyze_tags:", analyze_tags(citation_tags_json, ref_file_link))
                        print("DEBUG map_bolk_kolonneverdi:", map_bolk_kolonneverdi(ref_copyrights_status, ref_license_type, citation_tags_json, ref_file_link))
                        ref_bolk_kolonneverdi = map_bolk_kolonneverdi(
                            ref_copyrights_status, 
                            ref_license_type, 
                            citation_tags_json, 
                            ref_file_link, 
                            ref_isbnkommentar
                        )

                        try:
                            await c.execute("""
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
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """, (
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
        ref_isbnkommentar
    ))
                        except Exception as e:
                            print(f"Feil for referanse {ref_id} (pensumliste {rl_id}): {e}")

    # Hovedløkken for å hente og lagre alle kurs
    async def main(year="all"):
        async with aiohttp.ClientSession() as session:
            ids = await get_course_ids(session, year)
            print(f"Fant {len(ids)} kurs-IDer.")
            print(f"Unike kurs-IDer fra API: {len(set(ids))}")
            print(f"Totalt kurs-IDer fra API: {len(ids)}")
            sem = asyncio.Semaphore(CONCURRENT_REQUESTS)

            antall_ok = 0
            manglende = []

            async def fetch_and_insert(course_id):
                nonlocal antall_ok
                async with sem:
                    course_json = await fetch_course_detail(session, course_id)
                    if course_json:
                        await insert_to_db(pool, course_json)
                        antall_ok += 1
                    else:
                        manglende.append(course_id)

            tasks = [fetch_and_insert(cid) for cid in ids]
            for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Henter kursdetaljer", disable=True):
                await f
            print(f"Antall kurs med detaljer: {antall_ok}")
            print(f"Antall kurs uten detaljer: {len(manglende)}")
            if manglende:
                print("Eksempel på manglende kurs-IDer:", manglende[:10])

    await main(year)
  # OPTIMIZE TABLE etter alt er ferdig
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as c:
                await c.execute("""
                    OPTIMIZE TABLE 
                    api_alma_instructors, 
                    api_alma_kurs, 
                    api_alma_kurs_pensumlister_kobling, 
                    api_alma_pensumlister, 
                    api_alma_referanser, 
                    filoversikt_brukere, 
                    filoversikt_b_r, 
                    filoversikt_b_roller, 
                    filoversikt_data
                """)
        print("OPTIMIZE TABLE kjørt ferdig 👍")
    except Exception as e:
        print(f"Feil under OPTIMIZE TABLE: {e}")
