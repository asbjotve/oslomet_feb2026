import sys
import asyncio
import aiohttp
import json
import random
from config.config import settings
from app.database.db import get_async_db_pool
from dotenv import load_dotenv
from tqdm.asyncio import tqdm  # progresjonsbar

# Last inn miljøvariabler
load_dotenv(dotenv_path=".env.oslomet")

API_TOKEN = settings.ALMA_API_KEY
HEADERS = {
    'Accept': 'application/json',
    'Authorization': f'apikey {API_TOKEN}',
}

CONCURRENT_REQUESTS = 31  # Justér denne etter behov

def log_to_file(filename, content):
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Kunne ikke skrive til loggfil {filename}: {e}")

async def fetch_owner(session, url, id_, sem, progress, log_status):
    delay = 5.0
    last_status = None
    last_response = ""
    async with sem:
        for attempt in range(5):
            try:
                async with session.get(url, headers=HEADERS) as resp:
                    response_text = await resp.text()
                    last_status = resp.status
                    last_response = response_text
                    # Forsøk å dekode JSON uansett status
                    try:
                        data = json.loads(response_text)
                    except Exception:
                        data = {}
                    # Sjekk om errorCode 401873 finnes
                    error_401873 = False
                    if isinstance(data, dict) and data.get('errorsExist'):
                        errors = data.get('errorList', {}).get('error', [])
                        if isinstance(errors, list):
                            for err in errors:
                                if str(err.get('errorCode')) == "401873":
                                    error_401873 = True
                                    break
                    if error_401873:
                        owner_data = "401873"
                        log_to_file("response_log.txt", f"ID: {id_}\nRespons: errorCode=401873\nFull respons: {response_text}\n\n")
                        progress.update(1)
                        log_status['success'] += 1
                        return id_, owner_data, response_text
                    if resp.status == 200:
                        try:
                            if data == {}:
                                owner_data = ''
                            elif 'owner' in data:
                                full_names = [o.get('full_name') for o in data['owner'] if o.get('full_name')]
                                owner_data = ' ; '.join(full_names)
                            else:
                                owner_data = response_text
                        except Exception as e:
                            log_to_file("json_error_log.txt", f"ID: {id_}\nJSON Error: {str(e)}\nResponse: {response_text}\n\n")
                            owner_data = 'Invalid JSON'
                        log_to_file("response_log.txt", f"ID: {id_}\nResponse: {response_text}\n\n")
                        progress.update(1)
                        log_status['success'] += 1
                        return id_, owner_data, response_text
                    elif resp.status == 400:
                        log_to_file(
                            "fetch_error_log.txt",
                            f"ID: {id_}\n400 Bad Request\nRespons: {response_text}\nURL: {url}\n\n"
                        )
                        progress.update(1)
                        log_status['failed'] += 1
                        return id_, None, response_text
                    elif resp.status == 429:
                        print(f"ID {id_} ga status 429 (rate limit), venter {delay} sekunder (forsøk {attempt+1}/5)")
                        await asyncio.sleep(delay + random.uniform(0, 0.3))
                        delay *= 2
                    else:
                        if attempt == 4:
                            print(f"ID {id_} ga status {resp.status}")
                        await asyncio.sleep(0.2)
            except Exception as e:
                log_to_file("fetch_error_log.txt", f"ID: {id_}\nException: {str(e)}\nURL: {url}\n\n")
                await asyncio.sleep(0.2)
        log_to_file(
            "fetch_error_log.txt",
            f"ID: {id_}\nFeil: Ingen gyldig respons etter 5 forsøk\nSiste status: {last_status}\nSiste respons: {last_response}\nURL: {url}\n\n"
        )
        progress.update(1)
        log_status['failed'] += 1
        return id_, None, None

async def process_all_groups(url_list, pool):
    sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
    total = len(url_list)
    log_status = {'success': 0, 'failed': 0}
    async with aiohttp.ClientSession() as session:
        with tqdm(total=total, desc="Henter instruktører", unit="req") as progress:
            tasks = [
                fetch_owner(session, url, id_, sem, progress, log_status)
                for id_, url in url_list.items()
            ]
            results = []
            for f in asyncio.as_completed(tasks):
                res = await f
                results.append(res)
        print(f"FERDIG: {log_status['success']} OK / {log_status['failed']} feilet (se error-logger ved behov)")
        # Lagring til DB (asynkront)
        for id_, owner_data, response_text in results:
            print(f"Lagrer til db: id_={id_} owner_data={owner_data} response_text_length={len(str(response_text)) if response_text else 0}")
            if owner_data is None or response_text is None:
                continue  # Skip failed
            try:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        sql = """
                            INSERT INTO api_alma_instructors (id, owner, owner_json_raw)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                owner = VALUES(owner),
                                owner_json_raw = VALUES(owner_json_raw)
                        """
                        await cursor.execute(sql, (id_, owner_data, response_text))
                    await conn.commit()
                print(f"LAGRET id={id_}")
            except Exception as e:
                log_to_file("db_error_log.txt", f"ID: {id_}\nDatabase Error: {str(e)}\nResponse: {response_text}\n\n")
                print(f"DB-FEIL for id={id_}: {e}")

async def main():
    if len(sys.argv) <= 1:
        print("Argument mangler (forventet årstall eller 'all')")
        return

    year_input = sys.argv[1]
    if "," in year_input:
        print("Kun ett år om gangen er tillatt i dette scriptet. Håndter flere år i route/backend.")
        sys.exit(1)

    pool = await get_async_db_pool()

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if year_input == "all":
                    await cursor.execute("SELECT id, owner_url FROM api_alma_pensumlister")
                else:
                    await cursor.execute(
                        "SELECT id, owner_url FROM api_alma_pensumlister WHERE course_year = %s",
                        (year_input,)
                    )
                rows = await cursor.fetchall()
    except Exception as e:
        print(f"Kunne ikke koble til databasen eller hente data: {e}")
        pool.close()
        await pool.wait_closed()
        return

    if not rows:
        print("Ingen resultater")
        pool.close()
        await pool.wait_closed()
        return

    url_list = {row['id']: row['owner_url'] for row in rows}

    await process_all_groups(url_list, pool)

    # OPTIMIZE TABLE etter alt er ferdig
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
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

    pool.close()
    await pool.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
