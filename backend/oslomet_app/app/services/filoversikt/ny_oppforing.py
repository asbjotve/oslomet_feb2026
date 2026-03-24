import re
import time
import json
import datetime
import asyncio
from pathlib import Path

import aiomysql
from fastapi import HTTPException

# Regex for å validere filnavn på formatet ÅÅÅÅ_MM_DD_HHTT
FILNAVN_REGEX = re.compile(
    r"^(19|20)\d\d_(0[1-9]|1[0-2])_(0[1-9]|[12][0-9]|3[01])_([01][0-9]|2[0-3])[0-5][0-9]$"
)

# Hindrer at to requests skriver samme JSON-filer samtidig
_json_write_lock = asyncio.Lock()


def convert_datetime(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def query_and_save_to_json(conn: aiomysql.Connection, sql: str, params: tuple, output_file_path: str):
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(sql, params)
        rows = await cursor.fetchall()

    data = [{"fieldData": {k: (v if v is not None else "") for k, v in row.items()}} for row in rows]
    json_data = {"response": {"data": data}}

    output_file = Path(output_file_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    def _write():
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2, default=convert_datetime)

    await asyncio.to_thread(_write)


async def hent_brukerdata_med_token(token: str, cursor: aiomysql.DictCursor):
    await cursor.execute(
        "SELECT token_expiry, bruker_id, navn FROM filoversikt_brukere WHERE token = %s",
        (token,),
    )
    row = await cursor.fetchone()
    if not row:
        return None

    token_expiry = row.get("token_expiry")
    now = int(time.time())
    if token_expiry is None or token_expiry < now:
        return None

    return {"bruker_id": row["bruker_id"], "navn": row["navn"]}


async def leggtil_fil(fil, conn: aiomysql.Connection, cursor: aiomysql.DictCursor):
    if not getattr(fil, "filnavn", None):
        raise HTTPException(status_code=400, detail="Feltet for FILNAVN kan ikke være tomt")

    if not FILNAVN_REGEX.match(fil.filnavn):
        raise HTTPException(
            status_code=400,
            detail="Feil filformat for FILNAVN: Det skal være skrevet i formatet ÅÅÅÅ_MM_DD_HHTT (f.eks. 2024_09_02_1330)",
        )

    if not getattr(fil, "token", None):
        raise HTTPException(status_code=401, detail="Ingen token oppgitt")

    brukerdata = await hent_brukerdata_med_token(fil.token, cursor)
    if not brukerdata:
        raise HTTPException(status_code=401, detail="Ugyldig eller utløpt token")

    fil.lagt_til_av_id = brukerdata["bruker_id"]
    fil.lagt_til_av_navn = brukerdata["navn"]

    sql = """
        INSERT INTO filoversikt_data (
            filnavn, boktittel, artikkel_tittel, tittel, sideangivelse, kapittelnummer,
            kapittelforfatter, kapitteltittel, utgitt, forlag, forfatter, merknad, isbn, issn, kommentar, mangler_i_fil,
            skannjobb_id, type_dokument, tidsskrift, argang_volume, hefte_issue, fil_bestar_av,
            alternativ_sideangivelse, mange_sideangivelser, doktype_id, lagt_til_av_id, lagt_til_av_navn
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = (
        fil.filnavn, getattr(fil, "boktittel", None), getattr(fil, "artikkel_tittel", None), getattr(fil, "tittel", None),
        getattr(fil, "sideangivelse", None), getattr(fil, "kapittelnummer", None), getattr(fil, "kapittelforfatter", None),
        getattr(fil, "kapitteltittel", None), getattr(fil, "utgitt", None), getattr(fil, "forlag", None),
        getattr(fil, "forfatter", None), getattr(fil, "merknad", None), getattr(fil, "isbn", None),
        getattr(fil, "issn", None), getattr(fil, "kommentar", None), getattr(fil, "mangler_i_fil", None),
        getattr(fil, "skannjobb_id", None), getattr(fil, "type_dokument", None), getattr(fil, "tidsskrift", None),
        getattr(fil, "argang_volume", None), getattr(fil, "hefte_issue", None), getattr(fil, "fil_bestar_av", None),
        getattr(fil, "alternativ_sideangivelse", None), getattr(fil, "mange_sideangivelser", None),
        getattr(fil, "doktype_id", None), fil.lagt_til_av_id, fil.lagt_til_av_navn
    )

    try:
        await cursor.execute(sql, params)
        await conn.commit()
        inserted_id = cursor.lastrowid

    except aiomysql.IntegrityError as err:
        # Viktig ved autocommit=False
        try:
            await conn.rollback()
        except Exception:
            pass

        # typisk (1062, "Duplicate entry ...")
        if getattr(err, "args", None) and len(err.args) >= 1 and err.args[0] == 1062:
            filnavn = getattr(fil, "filnavn", "<ukjent>")
            raise HTTPException(
                status_code=409,
                detail=f"Filen '{filnavn}.pdf' er allerede registrert i oversikten",
            )

        raise HTTPException(status_code=500, detail=f"Databasefeil: {err}")

    except Exception:
        # Viktig ved autocommit=False
        try:
            await conn.rollback()
        except Exception:
            pass
        raise


    # JSON må oppdateres før response, og låses for å unngå samtidige writes
    async with _json_write_lock:
        await query_and_save_to_json(conn, "SELECT * FROM filoversikt_bokutdrag", (), "/var/www/oslomet.plexcityhub.net/json/bokutdrag.txt")
        await query_and_save_to_json(conn, "SELECT * FROM filoversikt_artikler", (), "/var/www/oslomet.plexcityhub.net/json/artikler.txt")
        await query_and_save_to_json(conn, "SELECT * FROM filoversikt_annet", (), "/var/www/oslomet.plexcityhub.net/json/annet.txt")
        await query_and_save_to_json(conn, "SELECT * FROM filoversikt_sammensatte_utdrag", (), "/var/www/oslomet.plexcityhub.net/json/sammensatt.txt")
        await query_and_save_to_json(conn, "SELECT * FROM filoversikt_unike_titler", (), "/var/www/oslomet.plexcityhub.net/json/json_bok_unik.txt")

    return {"id": inserted_id, "filnavn": fil.filnavn}
