from __future__ import annotations

import asyncio
import time
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.helpers.require_token import require_token
from app.database.db import get_async_db_pool

from app.services.alma_api.alle_data.hent_alle_data import import_alle_data_queue_worker
from app.services.alma_api.kurs.oppdater_kurs import oppdater_kurs
from app.services.alma_api.pensumlister.oppdater_pensumliste import oppdater_pensumliste
from app.services.alma_api.referanser.sync_referanser_for_pensumliste import sync_referanser_for_pensumliste
from app.services.alma_api.referanser.oppdater_referanse import oppdater_referanse

router = APIRouter()

# Hindrer at import startes to ganger samtidig i samme uvicorn-prosess.
_import_lock = asyncio.Lock()


@router.post("/alma_api/import", tags=["Alma API"])
async def alma_import(
    year: str = Query(..., description="År, kommaseparert liste (f.eks. '2026,2025') eller 'all'"),
    _deps=Depends(require_token),
):
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


@router.put("/alma_api/kurs/{kurs_id}", tags=["Alma API"])
async def alma_kurs_put(
    kurs_id: str,
    _deps=Depends(require_token),
):
    pool = await get_async_db_pool()

    try:
        return await oppdater_kurs(pool=pool, kurs_id=kurs_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Oppdatering feilet: {str(e)}", "kurs_id": kurs_id},
        ) from e

@router.put("/alma_api/pensumliste/{pensumliste_id}", tags=["Alma API"])
async def alma_pensumliste_put(
    pensumliste_id: str,
    _deps=Depends(require_token),
):
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

@router.put("/alma_api/pensumliste/{pensumliste_id}/referanser", tags=["Alma API"])
async def alma_pensumliste_referanser_put(
    pensumliste_id: str,
    _deps=Depends(require_token),
):
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


@router.put("/alma_api/referanse/{referanse_id}", tags=["Alma API"])
async def alma_referanse_put(
    referanse_id: str,
    _deps=Depends(require_token),
):
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
