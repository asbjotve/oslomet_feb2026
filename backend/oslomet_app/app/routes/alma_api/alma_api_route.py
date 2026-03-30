from __future__ import annotations

import logging
import asyncio
import time
from datetime import timedelta
import aiomysql

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Optional

from app.helpers.require_token import require_token
from app.helpers.alma_api import get_url_list, normalize_years_input

from app.database.db import get_async_db_pool

from app.services.alma_api.alle_data.hent_alle_data import import_alle_data_queue_worker
from app.services.alma_api.kurs.oppdater_kurs import oppdater_kurs
from app.services.alma_api.pensumlister.oppdater_pensumliste import oppdater_pensumliste
from app.services.alma_api.referanser.sync_referanser_for_pensumliste import sync_referanser_for_pensumliste
from app.services.alma_api.referanser.oppdater_referanse import oppdater_referanse
from app.services.alma_api.instructors.hent_instructors import process_instructors_urls

router = APIRouter()

# Hindrer at import startes to ganger samtidig i samme uvicorn-prosess.
_import_lock = asyncio.Lock()


@router.post("/alma_api/import", tags=["Alma API"], summary="Importer data fra ExLibris Alma")
async def alma_import(
    year: str = Query(..., description="År, kommaseparert liste (f.eks. '2026,2025') eller 'all'"),
    _deps=Depends(require_token),
):
    """
    Importerer data fra ExLibris Alma til lokal database - via Alma sitt API.

    - Krever autentisering
    - År som ønskes å importeres må oppgis. År kan angis slik (uten hermetegn):
      - 2026
      - 2024, 2025 (flere år kan angis, adskilt med komma)
      - all — dette importerer ALLE data uavhengig av årstall kurset er for.
    """

    year_input = (year or "").strip()
    if not year_input:
        raise HTTPException(status_code=400, detail="Query-parameter 'year' kan ikke være tom.")

    # Ikke start to importer samtidig i samme prosess
    if _import_lock.locked():
        raise HTTPException(status_code=409, detail="Import kjører allerede. Prøv igjen senere.")

    start = time.perf_counter()

    async with _import_lock:
        pool = await get_async_db_pool()

        try:
            await import_alle_data_queue_worker(
                pool=pool,
                year_input=year_input,
                concurrency=31,
                id_queue_maxsize=2000,
                polite_sleep_seconds=0.2,
                delete_existing_first=True,
            )

            elapsed = time.perf_counter() - start
            return {
                "status": "ok",
                "year_input": year_input,
                "duration_seconds": round(elapsed, 3),
                "duration_human": str(timedelta(seconds=int(elapsed))),
            }

        except Exception as e:
            elapsed = time.perf_counter() - start
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Import feilet: {str(e)}",
                    "year_input": year_input,
                    "duration_seconds": round(elapsed, 3),
                },
            ) from e


@router.post("/alma_api/hent_instructors", tags=["Alma API"], summary="Importer instructor-data fra ExLibris Alma")
async def oppdater_instructors(
    year: str = Query(..., description="År, kommaseparert liste, eller 'all'"),
    deps=Depends(require_token),
) -> dict[str, Any]:
    """
    Importerer instructors fra ExLibris Alma til lokal database - via Alma sitt API

    - Krever autentisering
    - Krever at data om kurs/pensumlister allerede er innhentet for det/de år man ønsker instructor-data for


    - År som ønskes å importeres må oppgis. År kan angis slik (uten hermetegn):
      - 2026
      - 2024, 2025 (flere år kan angis, adskilt med komma)
      - all — dette importerer ALLE data uavhengig av årstall kurset er for.
    """

    years = normalize_years_input(year)
    pool = await get_async_db_pool()

    resultater: list[dict[str, Any]] = []

    for y in years:
        y_label = "ALL" if y is None else y
        try:
            url_list = await get_url_list(pool, "all" if y is None else y)
            stats = await process_instructors_urls(url_list, pool)
            resultater.append({"year": y_label, "status": "ok", "stats": stats})
        except Exception as e:
            logger.exception("oppdater_instructors feilet year=%s", y_label)
            resultater.append({"year": y_label, "status": "error", "error": str(e)})

    # OPTIMIZE TABLE: anbefales ikke i request-path i prod. Flytt til admin-jobb/cron.
    return {"resultater": resultater}


@router.put("/alma_api/kurs/{kurs_id}", tags=["Alma API"], summary="Oppdater kursdata fra ExLibris Alma")
async def alma_kurs_put(
    kurs_id: str,
    _deps=Depends(require_token),
):
    """
    Oppdaterer data om kurs i lokal database fra ExLibris Alma - via Alma sitt API

    - Krever autentisering
    - Krever oppgitt kurs-ID
    """

    pool = await get_async_db_pool()

    try:
        return await oppdater_kurs(pool=pool, kurs_id=kurs_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Oppdatering feilet: {str(e)}", "kurs_id": kurs_id},
        ) from e


@router.put("/alma_api/kurs/by_pensumliste/{pensumliste_id}", tags=["Alma API"], summary="Oppdater kursdata fra ExLibris Alma")
async def alma_kurs_by_pensumliste_put(
    pensumliste_id: str,
    _deps=Depends(require_token),
):
    """
    Oppdaterer data om kurs i lokal database fra ExLibris Alma - via Alma sitt API

    - Krever autentisering
    - Krever oppgitt pensumliste-ID
    - kurs-ID hentes fra lokal database via api_alma_pensumlister-tabellen
    """

    pool = await get_async_db_pool()

    try:
        # Slå opp kurs_id basert på pensumliste_id
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as c:
                await c.execute(
                    "SELECT kurs_id FROM api_alma_pensumlister WHERE id = %s LIMIT 1",
                    (pensumliste_id,),
                )
                row = await c.fetchone()

        if not row or not row.get("kurs_id"):
            raise HTTPException(
                status_code=404,
                detail={"message": "Fant ikke kurs_id for pensumliste_id", "pensumliste_id": pensumliste_id},
            )

        kurs_id = str(row["kurs_id"])

        # Gjenbruk eksisterende service
        return await oppdater_kurs(pool=pool, kurs_id=kurs_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Oppdatering feilet: {str(e)}",
                "pensumliste_id": pensumliste_id,
            },
        ) from e


@router.put("/alma_api/pensumliste/{pensumliste_id}", tags=["Alma API"], summary="Oppdater pensumliste-data fra ExLibris Alma")
async def alma_pensumliste_put(
    pensumliste_id: str,
    _deps=Depends(require_token),
):
    """
    Oppdaterer pensumliste-data i lokal database med data fra ExLibris Alma - via Alma sitt API

    - Krever autentisering
    - Pensumliste-ID må oppgis (og det forutsettes at pensumlisten allerede eksisterer i lokal database)
    """

    pool = await get_async_db_pool()

    try:
        return await oppdater_pensumliste(pool=pool, pensumliste_id=pensumliste_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail={"message": str(e), "pensumliste_id": pensumliste_id}) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Oppdatering feilet: {str(e)}", "pensumliste_id": pensumliste_id},
        ) from e

@router.put("/alma_api/pensumliste/{pensumliste_id}/referanser", tags=["Alma API"], summary="Oppdater/hent referanser fra ExLibris Alma")
async def alma_pensumliste_referanser_put(
    pensumliste_id: str,
    _deps=Depends(require_token),
):
    """
    Oppdaterer referanse-data i en gitt pensumliste i lokal database med data fra ExLibris Alma - via Alma sitt API

    - Krever autentisering
    - Krever Pensumliste-ID (og det forutsettes at pensumlisten allerede eksisterer i lokal database)
    """

    pool = await get_async_db_pool()

    try:
        return await sync_referanser_for_pensumliste(pool=pool, pensumliste_id=pensumliste_id)
    except LookupError as e:
        # DB-oppslag feiler eller pensumlisten finnes ikke i Alma-responsen
        raise HTTPException(
            status_code=404,
            detail={"message": str(e), "pensumliste_id": pensumliste_id},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Oppdatering feilet: {str(e)}", "pensumliste_id": pensumliste_id},
        ) from e


@router.put("/alma_api/referanse/{referanse_id}", tags=["Alma API"], summary="Oppdater/hent referanse fra ExLibris Alma")
async def alma_referanse_put(
    referanse_id: str,
    _deps=Depends(require_token),
):
    """
    Oppdaterer en enkelt-referanse i lokal database med data fra ExLibris Alma - via Alma sitt API

    - Krever autentisering
    - Krever Referanse-ID (og det forutsettes at referansen allerede eksisterer i lokal database)
    """

    pool = await get_async_db_pool()

    try:
        return await oppdater_referanse(pool=pool, referanse_id=referanse_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail={"message": str(e), "referanse_id": referanse_id}) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Oppdatering feilet: {str(e)}", "referanse_id": referanse_id},
        ) from e
