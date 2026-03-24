import aiomysql

async def slett_eksisterende_data(pool, year):
    async with pool.acquire() as conn:
        async with conn.cursor() as c:
            if year == "all":
                await c.execute("TRUNCATE TABLE api_alma_kurs")
                await c.execute("TRUNCATE TABLE api_alma_pensumlister")
                await c.execute("TRUNCATE TABLE api_alma_referanser")
                await c.execute("TRUNCATE TABLE api_alma_kurs_pensumlister_kobling")
            else:
                await c.execute("DELETE FROM api_alma_kurs WHERE year = %s", (year,))
                await c.execute("DELETE FROM api_alma_pensumlister WHERE course_year = %s", (year,))
                await c.execute("DELETE FROM api_alma_referanser WHERE course_year = %s", (year,))
                await c.execute("DELETE FROM api_alma_kurs_pensumlister_kobling WHERE aar = %s", (year,))

async def hent_referanse(pool, referanse_id, year=None, import_alle_data_func=None):
    """
    Sjekk om referanse finnes i databasen. Hvis ikke, importer alle data for gitt år.
    Returnerer kurs_id og pensumliste_id hvis funnet, ellers None.
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as c:
            await c.execute("SELECT kurs_id, pensumliste_id FROM api_alma_referanser WHERE id = %s", (referanse_id,))
            result = await c.fetchone()
            if result:
                return result["kurs_id"], result["pensumliste_id"]
            else:
                if import_alle_data_func and year:
                    print(f"Fant ikke referanse {referanse_id} i databasen. Importerer alle data for år {year} ...")
                    await import_alle_data_func(year)
                    await c.execute("SELECT kurs_id, pensumliste_id FROM api_alma_referanser WHERE id = %s", (referanse_id,))
                    result = await c.fetchone()
                    if result:
                        return result["kurs_id"], result["pensumliste_id"]
                print(f"Referanse {referanse_id} ble ikke funnet etter import.")
                return None, None
