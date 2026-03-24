import json
import base64
from dateutil.parser import parse as dateparse
import re
import unicodedata
from datetime import date
from pathlib import Path

def analyze_tags(citation_tags, file_link):
    verdi_1 = 0
    verdi_2 = 0
    verdi_3 = 0

    tags = []
    if isinstance(citation_tags, dict) and "citation_tag" in citation_tags:
        tags = citation_tags["citation_tag"]
    elif isinstance(citation_tags, list):
        tags = citation_tags

    # Første pass: sjekk konkrete verdier
    for tag in tags:
        value = (tag.get("value") or {}).get("value")
        if value == "DIGITIZED":
            verdi_1 = 1
        elif value == "DIGITIZATION":
            verdi_2 = 3
        elif value == "Klarert":
            verdi_3 = 5

    verdi = verdi_1 + verdi_2 + verdi_3

    # Andre pass: hvis ingen av de over traff
    if verdi == 0:
        if not file_link:  # dekker "" og None
            return 0

        has_clearance_approval = any(
            ((tag.get("value") or {}).get("value") == "CLEARANCE_APPROVAL")
            for tag in tags
        )
        return 13 if has_clearance_approval else 12

    return verdi

def analyze_tags(citation_tags, file_link):
    verdi_1 = 0
    verdi_2 = 0
    verdi_3 = 0

    tags = []
    if isinstance(citation_tags, dict) and "citation_tag" in citation_tags:
        tags = citation_tags["citation_tag"]
    elif isinstance(citation_tags, list):
        tags = citation_tags

    # Normaliser tag-verdier
    values = [((tag.get("value") or {}).get("value")) for tag in tags]

    has_digitized = "DIGITIZED" in values
    has_digitization = "DIGITIZATION"
    has_clearance_approval = "CLEARANCE_APPROVAL" in values  # hvis det egentlig er denne som finnes i data

    # Ønsket spesialregel:
    # returner 13 hvis DIGITIZED + clearance + file_link mangler
    if (has_digitized or has_digitization) and has_clearance_approval and not file_link:
        return 13

    # Eksisterende logikk (som før)
    for value in values:
        if value == "DIGITIZED":
            verdi_1 = 1
        elif value == "DIGITIZATION":
            verdi_2 = 3
        elif value == "Klarert":
            verdi_3 = 5

    return verdi_1 + verdi_2 + verdi_3
def analyze_tags_bolk(citation_tags):
    verdi = 0

    tags = []
    if isinstance(citation_tags, dict) and "citation_tag" in citation_tags:
        tags = citation_tags["citation_tag"]
    elif isinstance(citation_tags, list):
        tags = citation_tags

    for tag in tags:
        value = tag.get("value", {}).get("value")
        if value == "CLEARANCE_APPROVAL":
              verdi = 1
        else:
            verdi = 0

    return verdi

def safe(val, default=""):
    return val if val not in [None, ""] else default

def get_nested(d, keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d

# Konverter dato fra API til SQL-format, fallback til 1970 hvis ugyldig
def prepare_date(date_str):
    if not date_str:
        return "1970-01-01 00:00:00"
    date_str = date_str.replace("Z", "")
    try:
        return dateparse(date_str).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "1970-01-01 00:00:00"

# Konverter år til int, fallback til 0 hvis tomt
def prepare_year(year):
    return int(year) if year else 0

# Hent filnavn og filendelse fra URL slik det gjøres i PHP-scriptet
def process_url(file_link):
    if not file_link:
        return {"filnavn": None, "filendelse": ""}
    utdata = file_link.replace("%3A", ":")
    tekststreng = "eu01.prod.alma.dc03.hosted.exlibrisgroup.com:1801"
    url_bases = [
        "https://s3.eu-central-1.amazonaws.com/eu-st01.ext.exlibrisgroup.com/47BIBSYS_HIOA/storage/leganto/",
        "https://eu-st01.ext.exlibrisgroup.com/47BIBSYS_HIOA/storage/leganto/"
    ]
    for url_base in url_bases:
        if utdata.startswith(url_base):
            utdata = utdata[len(url_base):]
            break
    pos = utdata.find("?")
    if pos != -1:
        utdata = utdata[:pos]
    tekststreng_forekomst = tekststreng in utdata
    utdata_2 = utdata[37:] if len(utdata) > 37 else utdata
    utdata_position = utdata.find(tekststreng)
    if utdata_position != -1:
        utdata_1 = utdata[utdata_position + len(tekststreng):]
        utdata_1 = utdata_1.replace(tekststreng, "")
    else:
        utdata_1 = None
    utdata_final = utdata_1 if tekststreng_forekomst else utdata_2
    p = Path(utdata_final)
    filnavn = p.stem
    filendelse = p.suffix.lstrip(".")
    return {"filnavn": filnavn, "filendelse": filendelse}

def filter_string(string, allowed_chars):
    string = string.lower()
    return ''.join(c for c in string if c in allowed_chars)

def substitute(text):
    substitutions = {
        'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5', 'f': '6', 'g': '7', 'h': '8', 'i': '9', 'j': '10',
        'k': '11', 'l': '12', 'm': '13', 'n': '14', 'o': '15', 'p': '16', 'q': '17', 'r': '18', 's': '19', 't': '20',
        'u': '21', 'v': '22', 'w': '23', 'x': '24', 'y': '25', 'z': '26', 'æ': '27', 'ø': '28', 'å': '29', ' ': '-',
        'é': '30', 'ä': '31', 'ö': '32', 'ü': '33', 'á': '34'
    }
    return ''.join(substitutions.get(c, c) for c in text)

def split_string(input_str):
    length = len(input_str)
    part1 = input_str[:33]
    part2 = input_str[max(0, (length // 2) - 1):(length // 2) + 32]
    part3 = input_str[-33:]
    return part1 + part2 + part3

def split_string_utdrag(input_str):
    length = len(input_str)
    part1 = input_str[:32]
    part2 = input_str[max(0, (length // 2) - 1):(length // 2) + 31]
    part3 = input_str[-32:]
    return part1 + part2 + part3

def process_unik_bok_id(title, publication_date, publisher, citation_id):
    allowed_chars = '0123456789abcdefghijklmnopqrstuvwxyzæøåéäöüá '
    input_str = f"{title or ''}{publication_date or ''}{publisher or ''}"
    # Remove non-ASCII
    input_str = unicodedata.normalize('NFKD', input_str).encode('ascii', 'ignore').decode()
    lowercase_input = filter_string(input_str, allowed_chars)
    substituted_string = substitute(lowercase_input)
    string_over100 = split_string(substituted_string)
    if not substituted_string:
        streng = citation_id or ''
    elif len(substituted_string) > 100:
        streng = string_over100
    else:
        streng = substituted_string
    return streng

def process_unik_utdrag_id(title, kaptitt, kapforf, kapnr, sitnote, publication_year):
    allowed_chars = '0123456789abcdefghijklmnopqrstuvwxyzæøåéäöüá'
    allowed_chars_year = '0123456789'
    pub_year = ''.join(c for c in str(publication_year or '') if c in allowed_chars_year)[:4]
    input_str = f"{title or ''}{kaptitt or ''}{kapforf or ''}{kapnr or ''}{sitnote or ''}"
    # Remove non-ASCII
    input_str = unicodedata.normalize('NFKD', input_str).encode('ascii', 'ignore').decode()
    lowercase_input = filter_string(input_str, allowed_chars)
    string_over100 = split_string_utdrag(lowercase_input)
    lowercase_input = lowercase_input + pub_year
    if len(lowercase_input) > 100:
        streng = string_over100 + pub_year
    else:
        streng = lowercase_input
    return streng

def extract_numbers(string):
    if not string:
        return 0
    num = re.sub(r"\D", "", str(string))
    return int(num) if num else 0

def build_json_from_ref_vars(
    ref_sam_sideangivelse,
    ref_year, ref_publication_date, ref_public_note,
    ref_chapter_title, ref_chapter, ref_chapter_author
):
    if str(ref_year) == "0" or ref_year == 0:
        utgitt = ''.join(filter(str.isdigit, str(ref_publication_date)))
    else:
        utgitt = str(ref_year)

    result = {
        "utgitt": utgitt,
        "sideangivelse": ref_sam_sideangivelse,
        "siteringsnote": ref_public_note,
        "kapitteltittel": ref_chapter_title,
        "kapittelnummer": ref_chapter,
        "kapittelforfatter": ref_chapter_author
    }

    json_str = json.dumps(result, ensure_ascii=False)
    base64_str = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
    return base64_str

def validate_filelink(ref_file_link):
    # Sjekk om filnavnet matcher mønsteret "YYYY_MM_DD_HHMM"
    match = re.match(r"^\d{4}_\d{2}_\d{2}_\d{4}", ref_file_link or "")
    _beregning = 1 if match else 0

    # Filtrer ut kun tall fra filnavnet
    digits = ''.join(filter(str.isdigit, ref_file_link or ""))

    # Hent ut år, måned, dag, timeminutt
    _aar = int(digits[0:4]) if len(digits) >= 4 else 0
    _maned = int(digits[4:6]) if len(digits) >= 6 else 0
    _dato = int(digits[6:8]) if len(digits) >= 8 else 0
    _timeminutt = int(digits[8:12]) if len(digits) >= 12 else 0

    _stop_year = date.today().year + 1

    _aar_case = 1 if (2017 <= _aar < _stop_year) else 0
    _maned_case = 1 if (1 <= _maned < 13) else 0
    _dato_case = 1 if (1 <= _dato < 32) else 0
    _timeminutt_case = 1 if (1 <= _timeminutt < 2400) else 0

    _utregning_case = _beregning * _aar_case * _maned_case * _dato_case * _timeminutt_case

    return _utregning_case

def generer_import_kommentar(indikator_vaar_fil, file_link, citation_tags):
    if isinstance(citation_tags, int):
        tags = [citation_tags]
    elif isinstance(citation_tags, list):
        tags = citation_tags
    elif isinstance(citation_tags, str):
        tags = [int(t.strip()) for t in citation_tags.split(",") if t.strip().isdigit()]
    else:
        tags = []

    kommentar = ""

    if not file_link:
        if 3 in tags:
            kommentar = ""
        elif 4 in tags:
            kommentar = '- import-kommentar: tagget både DIGITIZED og DIGITIZATION, men uten fil'
        elif 1 in tags:
            kommentar = '- Tagget "Digitalisert", men er uten fil. Filen er enten fjernet - eller så er referansen oppdatert/lagt til på ny, uten fil.'
    else:
        if any(t in tags for t in [1, 3, 4]) and indikator_vaar_fil == 0:
            kommentar = '- import-kommentar: tagget, men filen er ikke produsert av UB'
        elif not any(t in tags for t in [1, 3, 4, 5, 6, 7, 9]) and indikator_vaar_fil == 0:
            kommentar = '- import-kommentar: ikke tagget, men har fil knyttet til referansen (som ikke er produsert av UB)'
        elif not any(t in tags for t in [1, 3, 4, 5, 6, 8, 9]) and indikator_vaar_fil == 1:
            kommentar = '- import-kommentar: Mangler tagg, men med fil produsert av UB'

# Mangler egentlig kommentar, dersom en referanse er tagget, men der filen er prousert av UB


    return kommentar

def map_academic_department(academic_department):
    if not academic_department:
        return "Uspesifisert"
    if "215_13" in academic_department:
        return "HV"
    if "215_14" in academic_department:
        return "LUI"
    if "215_15" in academic_department:
        return "SAM"
    if "215_16" in academic_department:
        return "TKD"
    return "Uspesifisert"

def sammensatt_sideangivelse(*pages):
    """
    Tar inn start_page1, end_page1, start_page2, end_page2, ..., start_page10, end_page10
    og returnerer en streng på formen: "start1-end1,start2-end2,..."
    Hopper over tomme start_page.
    """
    resultater = []
    for i in range(0, len(pages), 2):
        start = pages[i]
        end = pages[i+1] if i+1 < len(pages) else ""
        if start:
            value = f"{start}-{end}" if end else f"{start}-"
            resultater.append(value)
    return ",".join(resultater)

def map_secondary_type(secondary_type):
    """
    Returnerer 2 for artikler/tidsskrifter/aviser, 1 for bøker/kapitler/utdrag/score, ellers 3.
    """
    if not secondary_type:
        return 3
    type_map_2 = {
        "E_CR", "Electronic Article", "JR", "Journal", "NEWSPAPER_ARTICLE", "Newspaper Article",
        "NP", "Newspaper", "CR", "Article"
    }
    type_map_1 = {
        "Book", "BK", "Book Chapter", "BK_C", "Book Extract", "BOOK_EXTRACT", "Score", "SCORE"
    }
    if secondary_type in type_map_2:
        return 2
    if secondary_type in type_map_1:
        return 1
    return 3

def strip_tags(text):
    """
    Fjerner alle HTML-tagger og erstatter &nbsp; og nbsp; med mellomrom.
    """
    if not text:
        return ""
    # Fjern HTML-tagger
    text = re.sub(r"<[^>]+>", "", str(text))
    # Erstatt &nbsp; og nbsp; med mellomrom
    text = text.replace("&nbsp;", " ")
    text = text.replace("nbsp;", " ")
    return text.strip()

# Eksempel på bruk:
# sideangivelse = sammensatt_sideangivelse(
#     ref_start_page, ref_end_page,
#     ref_start_page2, ref_end_page2,
#     ref_start_page3, ref_end_page3,
#     ref_start_page4, ref_end_page4,
#     ref_start_page5, ref_end_page5,
#     ref_start_page6, ref_end_page6,
#     ref_start_page7, ref_end_page7,
#     ref_start_page8, ref_end_page8,
#     ref_start_page9, ref_end_page9,
#     ref_start_page10, ref_end_page10
# )

def map_bolk_kolonneverdi(copyrights_status, license_type, citation_tags, file_link=None, isbnkommentar=0):
    """
    Returnerer:
        1 hvis alle disse er oppfylt:
            - copyrights_status == "APPROVED"
            - license_type == "BOLK"
            - analyze_tags(citation_tags, file_link) == 1
        2 hvis begge disse er oppfylt:
            - copyrights_status == "DECLINED"
            - analyze_tags(citation_tags, file_link) == 1
        3 hvis:
            - analyze_tags(citation_tags, file_link) == 1
            - copyrights_status er IKKE "DECLINED" eller "APPROVED"
        4 for alle andre tilfeller
    """
    tags_result = analyze_tags(citation_tags, file_link)

#    if copyrights_status == "APPROVED" and license_type == "BOLK" and tags_result == 1:
#        return 1
#    elif copyrights_status == "DECLINED" and tags_result == 1:
#        return 2
#    elif tags_result == 1 and copyrights_status not in ("DECLINED", "APPROVED"):
#        return 3
#    else:
#        return 4

# Koden nedenfor erstatter koden overfor, ny kode lagt til 16.12.2026
    if copyrights_status == "APPROVED" and tags_result == 1 and (license_type is None or license_type == "") and isbnkommentar == 0:
        return 4
    elif copyrights_status == "APPROVED" and license_type == "BOLK" and tags_result == 1 and isbnkommentar == 0:
        return 1
    elif copyrights_status == "DECLINED" and tags_result == 1 and isbnkommentar == 0:
        return 2
    elif tags_result == 1 and copyrights_status not in ("DECLINED", "APPROVED") and isbnkommentar == 0:
        return 3
    else:
        return 5

def has_isbn_in_content(ref_note):
    """
    Sjekker om 'u/isbn' finnes i content-feltet i ref_note arrayet.
    
    Args:
        ref_note: JSON string eller Python list/dict med note-data
    
    Returns:
        1 hvis 'u/isbn' finnes i noen content, ellers 0
    """
    import json
    
    # Håndter tilfelle hvor ref_note er None
    if ref_note is None:
        return 0
    
    # Hvis ref_note er en JSON string, parse den
    if isinstance(ref_note, str):
        try:
            note_data = json.loads(ref_note)
        except (json.JSONDecodeError, ValueError):
            return 0
    else:
        note_data = ref_note
    
    # Sjekk om note_data er en liste
    if not isinstance(note_data, list):
        return 0
    
    # Iterer gjennom arrayet og sjekk content
    for item in note_data:
        if isinstance(item, dict) and "content" in item:
            content = item.get("content", "")
            if content and "u/isbn" in content:
                return 1
    
    return 0
