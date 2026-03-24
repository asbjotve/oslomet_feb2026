"""
helpers.py

Samler hjelpefunksjoner for filhåndtering, Google Sheets, MySQL, og databehandling.
Bruk denne modulen for felles funksjonalitet på tvers av scripts.
"""

import os
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import format_cell_range, CellFormat, NumberFormat
import gspread.utils
from oauth2client.service_account import ServiceAccountCredentials
import csv
import mysql.connector
import base64
import re
import html

# --- Filhåndtering og CSV ---
def check_csv_file(csv_fil, long_text_cols):
    """
    Sjekker om CSV-fil finnes og har data. Leser inn som DataFrame.
    Args:
        csv_fil: sti til CSV-fil
        long_text_cols: kolonner som skal tolkes som tekst
    Returns:
        DataFrame eller None
    """
    if not os.path.isfile(csv_fil):
        print(f"Filen '{csv_fil}' finnes ikke. Avbryter oppdatering.")
        return None
    try:
        csv_df = pd.read_csv(csv_fil, dtype={col: str for col in long_text_cols}).fillna("")
    except Exception as e:
        print(f"Kunne ikke lese CSV-filen '{csv_fil}': {e}")
        return None
    if csv_df.empty or len(csv_df) == 0:
        print(f"CSV-filen '{csv_fil}' er tom. Ingen oppdatering blir gjort.")
        return None
    return csv_df

# --- Google Sheets autentisering ---
def authenticate_gspread(credentials_path):
    """
    Autentiserer mot Google Sheets med service-account.
    Args:
        credentials_path: sti til credentials.json
    Returns:
        gspread client
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc

# --- Google Sheets formatering ---
def format_text_columns(worksheet, header, long_text_cols):
    """
    Formaterer utvalgte kolonner som tekst i Google Sheets.
    Args:
        worksheet: gspread worksheet-objekt
        header: liste over kolonnenavn
        long_text_cols: kolonner som skal formateres som tekst
    """
    for col in long_text_cols:
        if col in header:
            col_idx = header.index(col) + 1
            col_letter = gspread.utils.rowcol_to_a1(1, col_idx)[0]
            format_cell_range(
                worksheet,
                f"{col_letter}2:{col_letter}",
                CellFormat(numberFormat=NumberFormat(type='TEXT', pattern='@'))
            )

# --- JSON-hjelp ---
def read_json(filepath):
    """
    Leser inn JSON-fil og returnerer som dict.
    Args:
        filepath: sti til JSON-fil
    Returns:
        dict
    """
    with open(filepath, "r", encoding="utf-8") as fil:
        return json.load(fil)

# --- Google Sheets: hent og lagre som CSV ---
def hent_sheet_og_lagre_csv(service_account_file, spreadsheet_id, sheet_name, filnavn):
    """
    Henter data fra Google Sheet og lagrer som CSV.
    Args:
        service_account_file: sti til service-account json
        spreadsheet_id: Google Sheet ID
        sheet_name: navn på ark
        filnavn: output CSV-fil
    """
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    rows = sheet.get_all_values()
    with open(filnavn, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Data fra Google Sheet lagret som {filnavn}.")

# --- Filtrering av CSV ---
def filtrer_unike_ider_fra_forste_kolonne(fil_med_ider, fil_b, ny_fil):
    """
    Fjerner rader fra fil_b der ID finnes i fil_med_ider. Skriver resultat til ny_fil.
    Args:
        fil_med_ider: CSV med IDer
        fil_b: CSV som skal filtreres
        ny_fil: output-fil
    """
    with open(fil_med_ider, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        id_set = {row[0] for row in reader if row}
    with open(fil_b, newline='', encoding='utf-8') as f_in, \
         open(ny_fil, "w", newline='', encoding='utf-8') as f_out:
        reader = csv.reader(f_in)
        header = next(reader, None)
        writer = csv.writer(f_out)
        if header:
            writer.writerow(header)
        for row in reader:
            if row and row[0].strip() and row[0] not in id_set:
                writer.writerow(row)
    print(f"Filtrert fil lagret som {ny_fil}.")

# --- MySQL: hent og lagre som CSV ---
def hent_fra_mysql_og_lagre_csv_query(db_config, query, params, csv_fil, kolonner):
    """
    Kjører SQL-spørring mot MySQL og lagrer resultat som CSV.
    Args:
        db_config: dict med MySQL-params (host, user, password, database, etc)
        query: SQL-spørring
        params: parametre til spørring
        csv_fil: output-fil
        kolonner: kolonnenavn for CSV
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    with open(csv_fil, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(kolonner)
        writer.writerows(rows)
    cursor.close()
    conn.close()
    print(f"Data lagret som {csv_fil}.")

# --- MySQL: oppdater CSV med data fra tabell ---
def oppdater_csv_fra_mysql(
    csv_fil,
    mysql_config,
    mysql_tabell,
    kolonne_mapping,
    id_csv,
    id_mysql,
    output_fil=None
):
    """
    Oppdaterer rader i en CSV-fil med data fra MySQL, basert på mapping mellom kolonner.
    Args:
        csv_fil: sti til input-CSV
        mysql_config: dict med MySQL-params
        mysql_tabell: tabellnavn i MySQL
        kolonne_mapping: dict {csv_kolonne: mysql_kolonne}
        id_csv: kolonnenavn for unik id i CSV
        id_mysql: kolonnenavn for unik id i MySQL
        output_fil: hvis satt, lagre hit. Hvis None, lagres som 'oppdatert_' + basename(csv_fil)
    Returns:
        output-filnavn
    """
    # Sjekk om filen finnes
    if not os.path.isfile(csv_fil):
        print(f"Filen '{csv_fil}' finnes ikke. Avbryter oppdatering.")
        return None
    # Les filen og sjekk om den har data (mer enn bare header)
    try:
        df_csv = pd.read_csv(csv_fil, dtype=str)
    except Exception as e:
        print(f"Kunne ikke lese CSV-filen '{csv_fil}': {e}")
        return None
    if df_csv.empty or len(df_csv) == 0:
        print(f"CSV-filen '{csv_fil}' er tom. Ingen oppdatering blir gjort.")
        return None
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    mysql_kolonner = [v for v in kolonne_mapping.values()]
    sporring = f"SELECT {id_mysql}, {', '.join(mysql_kolonner)} FROM {mysql_tabell}"
    cursor.execute(sporring)
    mysql_data = cursor.fetchall()
    mysql_dict = {str(row[id_mysql]): row for row in mysql_data}
    for idx, row in df_csv.iterrows():
        row_id = str(row[id_csv])
        if row_id in mysql_dict:
            for csv_col, mysql_col in kolonne_mapping.items():
                if csv_col == id_csv:
                    continue
                ny_verdi = mysql_dict[row_id][mysql_col]
                if pd.notna(ny_verdi):
                    df_csv.at[idx, csv_col] = ny_verdi
    if output_fil is None:
        dir_name = os.path.dirname(csv_fil)
        base = os.path.basename(csv_fil)
        output_fil = os.path.join(dir_name, "oppdatert_" + base) if dir_name else "oppdatert_" + base
    df_csv.to_csv(output_fil, index=False, encoding="utf-8-sig")
    cursor.close()
    conn.close()
    print(f"Oppdatering ferdig! Lagret som '{output_fil}'")
    return output_fil

# --- Endringsstring og databehandling ---
def hent_endringsstring(siteringsid, conn):
    """
    Henter endringsstring fra MySQL for gitt siteringsid.
    Args:
        siteringsid: unik id
        conn: MySQL-connection
    Returns:
        endringsstring (base64)
    """
    query = "SELECT referanse_endringssjekk_json FROM api_alma_referanser WHERE id = %s"
    cursor = conn.cursor()
    cursor.execute(query, (siteringsid,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    return None

def decode_json(b64str):
    """
    Dekoder base64-streng til JSON/dict.
    Args:
        b64str: base64-streng
    Returns:
        dict
    """
    try:
        decoded = base64.b64decode(b64str)
        return json.loads(decoded)
    except Exception:
        return {}

def nullstr(val):
    """
    Rensker og normaliserer tekstverdi for sammenligning.
    Args:
        val: inputverdi
    Returns:
        str
    """
    if val is None:
        return ""
    val = str(val)
    val = re.sub(r"(&nbsp;|\u00A0)", " ", val)
    val = html.unescape(val)
    val = val.strip()
    val = re.sub(r"\s+", " ", val)
    val = re.sub(r"kap\.\s", "kap ", val, flags=re.IGNORECASE)
    val = re.sub(r"\.$", "", val)
    if val == "":
        return ""
    return val

def sammenlign_felter(csv_json, db_json):
    """
    Sammenligner utvalgte felter mellom to dicts og returnerer liste over endrede felter.
    Args:
        csv_json: dict fra CSV
        db_json: dict fra DB
    Returns:
        liste med feltnavn som er endret
    """
    endret = []
    felter = [
        "kapittelnummer",
        "kapitteltittel",
        "kapittelforfatter",
        "siteringsnote",
        "utgitt",
        "sideangivelse"
    ]
    for felt in felter:
        if nullstr(csv_json.get(felt)) != nullstr(db_json.get(felt)):
            endret.append(felt)
    return endret

def get_google_sheets_service(service_account_file, scopes=None):
    """
    Oppretter og returnerer Google Sheets API service-objekt.
    Args:
        service_account_file: sti til service-account json
        scopes: liste over scopes (default: spreadsheets)
    Returns:
        service-objekt
    """
    if scopes is None:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    return service
