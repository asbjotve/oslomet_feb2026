from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from app.database.db import get_db_conn_and_cursor
from app.services.filoversikt.ny_oppforing import leggtil_fil

logger = logging.getLogger(__name__)
router = APIRouter()

class Fil(BaseModel):
    filnavn: str
    token: str
    boktittel: Optional[str] = None
    artikkel_tittel: Optional[str] = None
    tittel: Optional[str] = None
    sideangivelse: Optional[str] = None
    kapittelnummer: Optional[str] = None
    kapittelforfatter: Optional[str] = None
    kapitteltittel: Optional[str] = None
    utgitt: Optional[str] = None
    forlag: Optional[str] = None
    forfatter: Optional[str] = None
    merknad: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    kommentar: Optional[str] = None
    mangler_i_fil: Optional[str] = None
    skannjobb_id: Optional[str] = None
    type_dokument: Optional[str] = None
    tidsskrift: Optional[str] = None
    argang_volume: Optional[str] = None
    hefte_issue: Optional[str] = None
    fil_bestar_av: Optional[str] = None
    alternativ_sideangivelse: Optional[str] = None
    mange_sideangivelser: Optional[str] = None
    doktype_id: Optional[str] = None
    lagt_til_av_id: Optional[str] = None
    lagt_til_av_navn: Optional[str] = None

@router.post("/filoversikt/leggtil", tags=["Filoversikt"])
async def leggtil_bruker(fil: Fil, db=Depends(get_db_conn_and_cursor)):
    conn, cursor = db
    try:
        resultat = await leggtil_fil(fil, conn, cursor)
        return {"status": "ok", "resultat": resultat}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Feil i /filoversikt/leggtil")
        raise HTTPException(status_code=500, detail=str(e))
