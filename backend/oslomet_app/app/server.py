from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

from app.routes.filoversikt.filoversikt_route import router as filoversikt_router

from app.database.db import get_async_db_pool, close_async_db_pool, get_db_conn_and_cursor
import aiomysql
import time
from datetime import datetime

from pydantic import BaseModel
from config.config import settings

# Argon2id hashing (via argon2-cffi)
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

app = FastAPI()

# ------------------------------------------------------------------------------
# Swagger / OpenAPI security (Authorize-knapp)
# ------------------------------------------------------------------------------
# tokenUrl må peke på endepunktet som utsteder token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ------------------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------------------
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://filoversikt.tveitas.net",
    "https://app.plexcityhub.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # sett til False hvis du ikke bruker cookies/credentials i browser
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
# Start-verdier som ofte funker bra for web-innlogging.
# Juster etter maskinvare/krav.
ph = PasswordHasher(
    time_cost=2,
    memory_cost=102400,  # 100 MiB
    parallelism=8,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    # DoS-beskyttelse: begrens ekstremt lange passord.
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
async def get_user_by_valid_token(cursor: aiomysql.DictCursor, token: str) -> dict:
    """
    Slår opp token i filoversikt_brukere og sjekker token_expiry.
    Returnerer user-dict hvis OK. Kaster 401 ellers.
    """
    now_epoch = int(time.time())

    await cursor.execute(
        "SELECT bruker_id, passord, token_expiry FROM filoversikt_brukere WHERE token = %s",
        (token,),
    )
    user = await cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller utløpt token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.get("token_expiry") is None or user["token_expiry"] < now_epoch:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller utløpt token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    Brukes for Swagger-authorize og beskyttede admin-endepunkter.
    Her sjekker vi token mot statisk token i settings.
    """
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


@app.on_event("shutdown")
async def shutdown_event():
    await close_async_db_pool()


# ------------------------------------------------------------------------------
# Eksterne routes
# ------------------------------------------------------------------------------
app.include_router(filoversikt_router)

# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------
@app.get("/")
def root():
    return {"msg": "Velkommen til APIet!"}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Dette endepunktet gjør at Swagger UI kan bruke OAuth2 password flow:
    - trykk "Authorize" i Swagger
    - skriv inn username/password
    - Swagger kaller POST /token og lagrer Bearer-token
    """
    if form_data.username == "admin" and form_data.password == ADMIN_PASSWORD:
        token = settings.FASTAPI_TOKEN
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Feil brukernavn/passord")


# ------------------------- Eksisterende (token i body) -------------------------
@app.post("/brukerroller", tags=["OsloMet-digitalisering nettsted"], include_in_schema=False)
async def brukerroller(body: TokenBody, db=Depends(get_db_conn_and_cursor)):
    """
    Bakoverkompatibel: tar token i body.
    """
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
    """
    Bakoverkompatibel: tar token i body.
    OBS: Denne forventer at user["passord"] er en Argon2-hash.
    Hvis du har gamle bcrypt-hasher i databasen må du enten migrere eller støtte begge i en overgang.
    """
    conn, cursor = db

    user = await get_user_by_valid_token(cursor, data.token)

    if not verify_password(data.oldPassword, user["passord"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Feil gammelt passord.",
        )

    new_password_hash = hash_password(data.newPassword)

    await cursor.execute(
        "UPDATE filoversikt_brukere SET passord = %s WHERE bruker_id = %s",
        (new_password_hash, user["bruker_id"]),
    )
    await conn.commit()

    return {"success": True, "message": "Passordet ble endret"}


@app.post("/api/create_user", tags=["OsloMet-digitalisering nettsted"])
async def create_user(data: BrukerCreateRequest, db=Depends(get_db_conn_and_cursor)):
    """
    Ubeskyttet i originalen (samme som før).
    Hvis du ønsker å beskytte brukeropprettelse, bruk /api/create_user_auth (under).
    """
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


# ------------------------- Nye (Swagger-friendly) endpoints ---------------------
@app.post("/brukerroller_auth", tags=["OsloMet-digitalisering nettsted"])
async def brukerroller_auth(
    db=Depends(get_db_conn_and_cursor),
    _admin_token: str = Depends(require_admin_token),
    token: str = Depends(oauth2_scheme),
):
    """
    Swagger-friendly: token i Authorization-header.
    NB: Her bruker vi token fra header til å slå opp roller i DB (samme som body-varianten).
    _admin_token sørger for at Swagger-greia er synlig/krevd (Bearer auth).
    token-parameteret her er egentlig samme token som _admin_token, men vi lar det være eksplisitt.
    """
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
    """
    Swagger-friendly og beskyttet: krever Bearer-token (fra Swagger Authorize).
    """
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
