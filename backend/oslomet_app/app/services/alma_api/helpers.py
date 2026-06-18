import json
import base64
from dateutil.parser import parse as dateparse
import re
import unicodedata
from datetime import date
from pathlib import Path


# ============================================================================
# NY KODE (2026-05-05): Bitmask for DIGITIZED/DIGITIZATION/Klarert + clearance
# ============================================================================

def _normalize_tags(citation_tags):
    if isinstance(citation_tags, dict) and "citation_tag" in citation_tags:
        return citation_tags["citation_tag"] or []
    if isinstance(citation_tags, list):
        return citation_tags
    return []


def tag_value_basic(citation_tags, file_link) -> int:
    """
    Returnerer tallverdi basert på DIGITIZED/DIGITIZATION/Klarert.

    Bitverdier:
      DIGITIZED    -> 1
      DIGITIZATION -> 2
      Klarert      -> 4

    Spesialregel (som i gammel kode):
      - Hvis ingen av disse tre taggene finnes (mask == 0):
          - ingen fil  -> 0
          - har fil    -> 12
      - Ellers returneres mask (1..7).
    """
    tags = _normalize_tags(citation_tags)

    value_to_bit = {
        "DIGITIZED": 1,
        "DIGITIZATION": 2,
        "Klarert": 4,
    }

    mask = 0
    for tag in tags:
        v = (tag.get("value") or {}).get("value")
        mask |= value_to_bit.get(v, 0)

    if mask == 0:
        return 12 if file_link else 0

    return mask

def clearance_status(citation_tags) -> int:
    """
    Returnerer:
      1 hvis CLEARANCE_APPROVAL finnes
      2 hvis CLEARANCE_DECLINED finnes
      0 ellers
    """
    tags = _normalize_tags(citation_tags)

    for tag in tags:
        v = (tag.get("value") or {}).get("value")
        if v == "CLEARANCE_APPROVAL":
            return 1
        if v == "CLEARANCE_ACTION_REQUIRED":
            return 2
    return 0

# ============================================================================
# GAMMEL KODE (legacy): analyze_tags_OLD
# ============================================================================

def analyze_tags(citation_tags, file_link):
    har_fil = 47 if file_link else 0

    if isinstance(citation_tags, dict) and "citation_tag" in citation_tags:
        tags = citation_tags["citation_tag"] or []
    elif isinstance(citation_tags, list):
        tags = citation_tags
    else:
        tags = []

    value_to_score = {
        "DIGITIZED": 2,
        "DIGITIZATION": 5,
        "Klarert": 11,
        "CLEARANCE_APPROVAL": 23,
    }

    present_values = {
        (tag.get("value") or {}).get("value")
        for tag in tags
    }

    tagg_verdi = sum(value_to_score.get(v, 0) for v in present_values)
    return har_fil + tagg_verdi

def analyze_tags_OLD(citation_tags, file_link):
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

def analyze_tags_dublett(citation_tags, file_link):
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
    """Analyserer om referansen er bolk-behandlet eller ikke. Kan med fordel erstattes av 'clerance_status()' """
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
        if any(t in tags for t in [1, 2, 3]) and indikator_vaar_fil == 0:
            kommentar = '- import-kommentar: tagget, men filen er ikke produsert av UB'
        elif not any(t in tags for t in [1, 2, 3, 4, 5, 6, 7]) and indikator_vaar_fil == 0:
            kommentar = '- import-kommentar: ikke tagget, men har fil knyttet til referansen (som ikke er produsert av UB)'
        elif not any(t in tags for t in [1, 2, 3, 4, 5, 6, 7]) and indikator_vaar_fil == 1:
            kommentar = '- import-kommentar: Mangler tagg, men med fil produsert av UB'

# Mangler egentlig kommentar, dersom en referanse er tagget, men der filen er prousert av UB - er denne kommentaren
# nødvendig, pr. 06.05.2026?


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

def map_bolk_kolonneverdi(copyrights_status, citation_tags, bolk_tag, file_link=None, isbnkommentar=0):
    tags_result = tag_value_basic(citation_tags, file_link)

    tags_result = tag_value_basic(citation_tags, file_link)
    tags_ok = (tags_result == 1)
    has_file = bool(file_link)  # True hvis ikke None og ikke ""

    """
    Scriptet nedenfor har ulike tallverdier, som returneres på bakgrunn av flere verdier.
        1. Dette utløses på referanser som er rapportert via bolk, og er i orden - men hvor 
            det ikke er noe fil knyttet til referansen. Filen skal altså komme fra bolk/kopinor.
        2. Som over, men her har vi lastet opp fil, og ingen fil kommer fra bolk/kopinor.
        3. Dette uløses på referanser som har copyrights status "Approved" og tagg er "Digitalisert".
            Dette er med andre ord gjerne referanser som var rapportert til bolk/kopinor for fjoråret, 
            men ikke rapportert for inneværende år.
        4. Referanse som har feilet /gitt copyrights status "DECLINED"), og er rapportert til bolk/kopinor.
        5. Referanser som har feilet (gitt copyrights status "DECLINED", men ikke nødvendigvis faktisk er rapportert
            inn til bolk/kopinor.
        6. Referanser, hvor det er annen status enn DECLINED, APPROVED eller NOTDETERMINED.
        7. Referanser med statusen NOTDETERMINED - og som ikke nødvendigvis er rapportert inn til bolk/kopinor.
        8. Alle referanser som ikke er bolk-rapportert, har tagg som tilsier "DIGITIZED" OG har kommentar om at referansen er uten ISBN
    """

    if copyrights_status == "APPROVED" and bolk_tag == 1 and tags_ok and (not has_file) and isbnkommentar == 0:
        return 1
    elif copyrights_status == "APPROVED" and bolk_tag == 1 and tags_ok and has_file and isbnkommentar == 0:
        return 2
    elif copyrights_status == "APPROVED" and bolk_tag == 0 and tags_ok and has_file and isbnkommentar == 0:
        return 3
    elif copyrights_status == "DECLINED" and bolk_tag == 2 and tags_ok and has_file and isbnkommentar == 0:
        return 4
    elif copyrights_status == "DECLINED" and bolk_tag == 0 and tags_ok and has_file and isbnkommentar == 0:
        return 5
    elif copyrights_status not in ("DECLINED", "APPROVED", "NOTDETERMINED") and bolk_tag in (1, 2, 0) and tags_ok and has_file and isbnkommentar == 0:
        return 6
    elif copyrights_status == "NOTDETERMINED" and bolk_tag in (1, 2, 0) and tags_ok and has_file and isbnkommentar == 0:
        return 7
    elif bolk_tag == 0 and tags_ok and has_file and isbnkommentar == 1:
        return 8
    elif tags_result in (2,3):
        return 9
    else:
        return 10

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
