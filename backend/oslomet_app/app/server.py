import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import aiomysql
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel

from app.database.db import get_async_db_pool, close_async_db_pool, get_db_conn_and_cursor
from app.helpers.job_storage import cleanup_old_jobs
from app.routes.alma_api.alma_api_route import router as alma_api_router
from app.routes.arbeidsoversikt.arbeidsoversikt_sort_sheet import router as arbeidsoversikt_sort_sheet
from app.routes.arbeidsoversikt.sync_endringer_route import router as arbeidsoversikt_endringer_router
from app.routes.arbeidsoversikt.sync_reaktiverte_route import router as arbeidsoversikt_reaktiverte_router
from app.routes.arbeidsoversikt.sync_route import router as arbeidsoversikt_router
from app.routes.filoversikt.filoversikt_route import router as filoversikt_router

from app.routes.filoversikt.hent_bokutdrag import router as bokutdrag_router
from app.routes.filoversikt.hent_artikler import router as artikler_router
from app.routes.filoversikt.hent_annet_dok import router as annet_dok_router
from app.routes.filoversikt.hent_sammensatt import router as sammensatt_router

from app.routes.filoversikt.isbn_oppslag import router as isbn_oppslag_router
from app.routes.kopinor.kopinor_tall_route import router as kopinor_tall_router
from app.routes.kopinor.kopinor_referanser_route import router as kopinor_referanser_router
from app.routes.referansesjekk.referansesjekk_route import router as referansesjekk_router

from config.config import settings

# ------------------------------------------------------------------------------
# Logging av applikasjonen
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

# ------------------------------------------------------------------------------
# Demper støy/varsel ved import av dupliserte poster i databasen
# ------------------------------------------------------------------------------
import warnings

warnings.filterwarnings("ignore", message=r"Duplicate entry .*", category=Warning)
warnings.filterwarnings("ignore", message=r"Duplicate entry .*", category=UserWarning)

# ------------------------------------------------------------------------------
# Swagger / OpenAPI security (Authorize-knapp)
# ------------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ------------------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------------------
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://filoversikt.tveitas.net",
    "https://app.plexcityhub.net",
    "https://app.oslomet.plexcityhub.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------------------
ADMIN_PASSWORD = settings.ADMIN_PW

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------
class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str
    token: str


class BrukerCreateRequest(BaseModel):
    brukernavn: str
    passord: str
    navn: str


class TokenBody(BaseModel):
    token: str


# ------------------------------------------------------------------------------
# Password helpers (Argon2id)
# ------------------------------------------------------------------------------
ph = PasswordHasher(
    time_cost=2,
    memory_cost=102400,  # 100 MiB
    parallelism=8,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    if len(password) > 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Passordet er for langt (maks 1024 tegn).",
        )
    return ph.hash(password)


def verify_password(password: str, password_hash_from_db: str) -> bool:
    try:
        return ph.verify(password_hash_from_db, password)
    except VerifyMismatchError:
        return False


def needs_rehash(password_hash_from_db: str) -> bool:
    try:
        return ph.check_needs_rehash(password_hash_from_db)
    except Exception:
        return False


# ------------------------------------------------------------------------------
# Token / auth helpers
# ------------------------------------------------------------------------------
def _normalize_token(token: str) -> str:
    """
    Normaliser token fra klient/proxy.
    Fjerner whitespace og evt. anførselstegn rundt (hender hvis noe dobbel-json-encodes).
    """
    if token is None:
        return ""
    t = token.strip()
    # Hvis token kommer som '"abc..."' (inkl. anførselstegn), fjern dem
    if len(t) >= 2 and ((t[0] == '"' and t[-1] == '"') or (t[0] == "'" and t[-1] == "'")):
        t = t[1:-1].strip()
    return t


async def get_user_by_valid_token(cursor: aiomysql.DictCursor, token: str) -> dict:
    """
    Slår opp token i filoversikt_brukere og sjekker token_expiry.
    Returnerer user-dict hvis OK. Kaster 401 ellers.
    """
    now_epoch = int(time.time())

    token = (token or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller utløpt token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await cursor.execute(
        "SELECT bruker_id, token_expiry FROM filoversikt_brukere WHERE token = %s LIMIT 1",
        (token,),
    )
    user = await cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller utløpt token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    exp = user.get("token_expiry")
    if exp is None or int(exp) < now_epoch:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller utløpt token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

async def require_admin_token(token: str = Depends(oauth2_scheme)) -> str:
    if token != settings.FASTAPI_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


# ------------------------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    await get_async_db_pool()

    project_root = Path(__file__).resolve().parents[1]
    cleanup_stats = cleanup_old_jobs(project_root=project_root, keep_days=7)
    logger.info("job cleanup: %s", cleanup_stats)


@app.on_event("shutdown")
async def shutdown_event():
    await close_async_db_pool()


# ------------------------------------------------------------------------------
# Eksterne routes
# ------------------------------------------------------------------------------
app.include_router(filoversikt_router)
app.include_router(alma_api_router)
app.include_router(arbeidsoversikt_router)
app.include_router(arbeidsoversikt_endringer_router)
app.include_router(arbeidsoversikt_reaktiverte_router)
app.include_router(arbeidsoversikt_sort_sheet)
app.include_router(kopinor_tall_router)
app.include_router(kopinor_referanser_router)
app.include_router(referansesjekk_router)
app.include_router(bokutdrag_router)
app.include_router(artikler_router)
app.include_router(annet_dok_router)
app.include_router(sammensatt_router)
app.include_router(isbn_oppslag_router)

# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------
@app.get("/")
def root():
    return {"msg": "Velkommen til APIet!"}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == ADMIN_PASSWORD:
        token = settings.FASTAPI_TOKEN
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Feil brukernavn/passord")


@app.post("/brukerroller", tags=["OsloMet-digitalisering nettsted"], include_in_schema=False)
async def brukerroller(body: TokenBody, db=Depends(get_db_conn_and_cursor)):
    logger.info(
        "brukerroller received token len=%s prefix=%s",
        len(body.token) if body.token else 0,
        body.token[:12] if body.token else "",
    )

    _conn, cursor = db

    user = await get_user_by_valid_token(cursor, body.token)
    bruker_id = user["bruker_id"]

    await cursor.execute(
        """
        SELECT r.rolle
        FROM filoversikt_b_r AS br
        JOIN filoversikt_b_roller AS r ON br.rolle_id = r.rolle_id
        WHERE br.bruker_id = %s
        """,
        (bruker_id,),
    )
    roller = [row["rolle"].lower() for row in await cursor.fetchall()]
    if not roller:
        roller = ["user"]

    return {"roles": roller}


@app.post("/api/change_password", tags=["OsloMet-digitalisering nettsted"])
async def change_password(data: ChangePasswordRequest, db=Depends(get_db_conn_and_cursor)):
    conn, cursor = db

    token = _normalize_token(data.token)
    user = await get_user_by_valid_token(cursor, token)
    bruker_id = user["bruker_id"]

    # Hent passord-hash eksplisitt for denne brukeren
    await cursor.execute(
        "SELECT passord FROM filoversikt_brukere WHERE bruker_id = %s LIMIT 1",
        (bruker_id,),
    )
    row = await cursor.fetchone()
    if not row or not row.get("passord"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig bruker eller mangler passord.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(data.oldPassword, row["passord"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Feil gammelt passord.",
        )

    new_password_hash = hash_password(data.newPassword)

    await cursor.execute(
        "UPDATE filoversikt_brukere SET passord = %s WHERE bruker_id = %s",
        (new_password_hash, bruker_id),
    )
    await conn.commit()

    return {"success": True, "message": "Passordet ble endret"}

@app.post("/api/create_user", tags=["OsloMet-digitalisering nettsted"])
async def create_user(data: BrukerCreateRequest, db=Depends(get_db_conn_and_cursor)):
    conn, cursor = db

    await cursor.execute(
        "SELECT bruker_id FROM filoversikt_brukere WHERE brukernavn = %s",
        (data.brukernavn,),
    )
    existing_user = await cursor.fetchone()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Brukernavnet er allerede i bruk.",
        )

    hashed_password = hash_password(data.passord)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await cursor.execute(
        """
        INSERT INTO filoversikt_brukere (brukernavn, passord, navn, opprettet_tidspunkt)
        VALUES (%s, %s, %s, %s)
        """,
        (data.brukernavn, hashed_password, data.navn, now),
    )

    await cursor.execute("SELECT LAST_INSERT_ID() AS bruker_id")
    bruker = await cursor.fetchone()
    bruker_id = bruker["bruker_id"]

    await cursor.execute(
        "SELECT rolle_id FROM filoversikt_b_roller WHERE rolle = %s",
        ("Medarbeider",),
    )
    rolle = await cursor.fetchone()
    if not rolle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Standardrolle 'Medarbeider' finnes ikke i systemet.",
        )
    rolle_id = rolle["rolle_id"]

    await cursor.execute(
        "INSERT INTO filoversikt_b_r (bruker_id, rolle_id) VALUES (%s, %s)",
        (bruker_id, rolle_id),
    )
    await conn.commit()

    return {"success": True, "message": "Bruker opprettet og tildelt rolle!"}


@app.post("/brukerroller_auth", tags=["OsloMet-digitalisering nettsted"])
async def brukerroller_auth(
    db=Depends(get_db_conn_and_cursor),
    _admin_token: str = Depends(require_admin_token),
    token: str = Depends(oauth2_scheme),
):
    _conn, cursor = db

    user = await get_user_by_valid_token(cursor, token)
    bruker_id = user["bruker_id"]

    await cursor.execute(
        """
        SELECT r.rolle
        FROM filoversikt_b_r AS br
        JOIN filoversikt_b_roller AS r ON br.rolle_id = r.rolle_id
        WHERE br.bruker_id = %s
        """,
        (bruker_id,),
    )
    roller = [row["rolle"].lower() for row in await cursor.fetchall()]
    if not roller:
        roller = ["user"]

    return {"roles": roller}


@app.post("/api/create_user_auth", tags=["OsloMet-digitalisering nettsted"])
async def create_user_auth(
    data: BrukerCreateRequest,
    db=Depends(get_db_conn_and_cursor),
    _admin_token: str = Depends(require_admin_token),
):
    conn, cursor = db

    await cursor.execute(
        "SELECT bruker_id FROM filoversikt_brukere WHERE brukernavn = %s",
        (data.brukernavn,),
    )
    existing_user = await cursor.fetchone()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Brukernavnet er allerede i bruk.",
        )

    hashed_password = hash_password(data.passord)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await cursor.execute(
        """
        INSERT INTO filoversikt_brukere (brukernavn, passord, navn, opprettet_tidspunkt)
        VALUES (%s, %s, %s, %s)
        """,
        (data.brukernavn, hashed_password, data.navn, now),
    )

    await cursor.execute("SELECT LAST_INSERT_ID() AS bruker_id")
    bruker = await cursor.fetchone()
    bruker_id = bruker["bruker_id"]

    await cursor.execute(
        "SELECT rolle_id FROM filoversikt_b_roller WHERE rolle = %s",
        ("Medarbeider",),
    )
    rolle = await cursor.fetchone()
    if not rolle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Standardrolle 'Medarbeider' finnes ikke i systemet.",
        )
    rolle_id = rolle["rolle_id"]

    await cursor.execute(
        "INSERT INTO filoversikt_b_r (bruker_id, rolle_id) VALUES (%s, %s)",
        (bruker_id, rolle_id),
    )
    await conn.commit()

    return {"success": True, "message": "Bruker opprettet og tildelt rolle!"}
