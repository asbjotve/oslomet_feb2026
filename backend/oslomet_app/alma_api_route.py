from fastapi import APIRouter, Query, Depends, HTTPException
import aiomysql
from app.helpers.require_token import require_token
from app.helpers.hent_kursdata import get_url_list
from app.services.hent_kursdata.importer_alle_data import import_alle_data, fetch_course_detail_single, insert_single_course_to_db
from app.services.hent_kursdata.hent_instructors import log_to_file, fetch_owner, process_all_groups
from config.config import settings
import aiohttp
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/alma_api/kursdata", tags=["Alma API"])
async def hent_kursdata_main(year: str = Query(..., description="År eller 'all', eller kommaseparert liste"), deps=Depends(require_token)):
    """
    Kjør import_alle_data (samme som main.py -a <year>) via API.
    Støtter flere år, kommaseparert.
    """
    years = [y.strip() for y in year.split(',') if y.strip()]
    resultater = []
    pool = await aiomysql.create_pool(
        host=settings.DB_HOST,
        port=3306,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        autocommit=True
    )
    try:
        for y in years:
            try:
                await import_alle_data(pool, y)
                resultater.append({"year": y, "status": "ok"})
            except Exception as e:
                resultater.append({"year": y, "status": "error", "error": str(e)})
        return {"status": "ok", "resultater": resultater}
    finally:
        pool.close()
        await pool.wait_closed()

# Endepunkt: importer kurs fra Alma API basert på course_id og lagre til MySQL
@router.post("/alma_api/enkelt_kurs", tags=["Alma API"])
async def importer_kurs_by_id(course_id: str = Query(..., description="Kurs-ID fra Alma"), deps=Depends(require_token)):
    pool = await aiomysql.create_pool(
        host=settings.DB_HOST,
        port=3306,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        autocommit=True
    )
    try:
        async with aiohttp.ClientSession() as session:
            course_json = await fetch_course_detail_single(session, course_id)
            if not course_json:
                return JSONResponse(status_code=404, content={"status": "not found", "course_id": course_id})
            await insert_single_course_to_db(pool, course_json)
            return course_json #return {"status": "ok", "course_id": course_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})
    finally:
        pool.close()
        await pool.wait_closed()


@router.post("/alma_api/hent_instructors", tags=["Alma API"])
async def oppdater_instructors(
    year: str = Query(..., description="År eller kommaseparert liste"),
    deps=Depends(require_token)
):
    years = [y.strip() for y in year.split(",") if y.strip()]
    resultater = []
    pool = await aiomysql.create_pool(
        host=settings.DB_HOST,
        port=3306,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        #autocommit=True,
    )
    try:
        for y in years:
            try:
                url_list = await get_url_list(pool, y)
                await process_all_groups(url_list, pool)
                resultater.append({"year": y, "status": "ok"})
            except Exception as e:
                resultater.append({"year": y, "status": "error", "error": str(e)})

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

        return {"resultater": resultater}
    finally:
        pool.close()
        await pool.wait_closed()
