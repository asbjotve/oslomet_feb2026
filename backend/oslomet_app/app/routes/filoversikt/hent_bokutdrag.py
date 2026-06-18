from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database.db import get_db_conn_and_cursor
from app.services.filoversikt.hent_bokutdrag import get_bokutdrag_data

router = APIRouter()

@router.get("/filoversikt/hent_bokutdrag", tags=["Filoversikt"])
async def bokutdrag_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    column: Optional[str] = Query(None),
    sort: Optional[str] = Query("boktittel"),
    direction: Optional[str] = Query("asc"),
    use_regex: bool = Query(False),
    db=Depends(get_db_conn_and_cursor),
):
    _conn, cursor = db
    return await get_bokutdrag_data(
        cursor=cursor,
        page=page,
        page_size=page_size,
        search=search,
        column=column,
        sort=sort,
        direction=direction,
        use_regex=use_regex,
    )
