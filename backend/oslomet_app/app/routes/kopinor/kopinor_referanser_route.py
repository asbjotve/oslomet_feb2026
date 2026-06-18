from typing import Any, Literal, Tuple

import aiomysql
from fastapi import APIRouter, Depends, Path, Query

from app.database.db import get_db_conn_and_cursor
from app.services.kopinor.kopinor_referanser import (
    fetch_kopinor_referanser_for_pensumliste,
)

router = APIRouter(prefix="/kopinor", tags=["Kopinor"])

ReferanseType = Literal["fikses", "nye", "alle"]


@router.get("/referanser/{pensumliste_id}")
async def kopinor_referanser_for_pensumliste(
    pensumliste_id: int = Path(..., gt=0, description="Pensumliste-ID (må være > 0)"),
    type: ReferanseType = Query(..., description="Må være 'fikses', 'nye' eller 'alle'"),
    db: Tuple[Any, aiomysql.DictCursor] = Depends(get_db_conn_and_cursor),
):
    _conn, cursor = db
    return await fetch_kopinor_referanser_for_pensumliste(
        cursor,
        pensumliste_id=pensumliste_id,
        type=type,
    )
