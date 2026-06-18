from fastapi import APIRouter, Depends, HTTPException, Query

from app.database.db import get_db_conn_and_cursor
from app.services.filoversikt.isbn_oppslag import hent_bokdata_fra_isbn

router = APIRouter()

@router.get("/filoversikt/bokoppslag_isbn", tags=["Filoversikt"])
async def bokoppslag_isbn(
    isbn: str = Query(..., min_length=1),
    db=Depends(get_db_conn_and_cursor),
):
    _conn, cursor = db

    try:
        return await hent_bokdata_fra_isbn(cursor, isbn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
