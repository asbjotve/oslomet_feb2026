from typing import Any, Tuple

import aiomysql
from fastapi import APIRouter, Depends, Path, Query

from app.database.db import get_db_conn_and_cursor
from app.services.kopinor.kopinor_tall import fetch_kopinor_tall_for_aarsem
from app.services.kopinor.kopinor_tall_pensumliste import (
    fetch_kopinor_tall_for_pensumliste,
)

router = APIRouter(prefix="/kopinor", tags=["Kopinor"])


def normalize_aarsem(value: str) -> str:
    return (value or "").strip().upper().replace(" ", "")


@router.get("/tall/{aarsem}")
async def kopinor_tall(
    aarsem: str = Path(
        ...,
        min_length=3,
        max_length=32,
        description="År/semester, f.eks. 2026AUTUMN",
        examples=["2026AUTUMN"],
    ),
    fakultet: str = Query("ALLE", description="Fakultet-filter (ALLE|SAM|TKD,LUI,HV)"),
    variant: str = Query("ALLE", description="Variant (ALLE|SKAL_BOLKES|DECLINED|SKAL_LAASES)"),
    db: Tuple[Any, aiomysql.DictCursor] = Depends(get_db_conn_and_cursor),
):
    _conn, cursor = db
    aarsem_norm = normalize_aarsem(aarsem)

    return await fetch_kopinor_tall_for_aarsem(
        cursor,
        aarsem=aarsem_norm,
        fakultet=fakultet,
        variant=variant,
    )


@router.get("/tall/{aarsem}/{pensumliste_id}")
async def kopinor_tall_for_pensumliste(
    aarsem: str = Path(
        ...,
        min_length=3,
        max_length=32,
        description="År/semester, f.eks. 2026AUTUMN",
        examples=["2026AUTUMN"],
    ),
    pensumliste_id: int = Path(
        ...,
        gt=0,
        description="Pensumliste-ID (må være > 0)",
        examples=[12345],
    ),
    fakultet: str = Query("ALLE", description="Fakultet-filter (ALLE|SAM|TKD,LUI,HV)"),
    variant: str = Query("ALLE", description="Variant (ALLE|SKAL_BOLKES|DECLINED|SKAL_LAASES)"),
    db: Tuple[Any, aiomysql.DictCursor] = Depends(get_db_conn_and_cursor),
):
    _conn, cursor = db
    aarsem_norm = normalize_aarsem(aarsem)

    return await fetch_kopinor_tall_for_pensumliste(
        cursor,
        aarsem=aarsem_norm,
        pensumliste_id=pensumliste_id,
        fakultet=fakultet,
        variant=variant,
    )
