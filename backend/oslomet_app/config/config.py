from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
import os

ENV = os.getenv("OSLOMET_ENV", "dev")

# Finn alltid base_dir fra hvor config.py ligger (robust, uansett arbeidskatalog)
BASE_DIR = Path(__file__).resolve().parent

ENV_FILES = {
    "dev": BASE_DIR / ".oslomet",
    "prod": BASE_DIR / ".env.prod",
    "test": BASE_DIR / ".env.test",
}

class Settings(BaseSettings):
    APP_NAME: str = "OsloMet2 API"
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "db_"
    DB_NAME_TEST: str = "db_"
    ALMA_API_KEY: str = "key"
    FASTAPI_TOKEN: str = "key"
    MAL_ARBEIDSOVERSIKT_SHEETID: str = "sheet_id"
    ADMIN_PW: str = "din hemmelige nøkkel"
    # ... legg til flere settings etter behov

    class Config:
        env_file = str(ENV_FILES.get(ENV, BASE_DIR / ".env.dev"))
        env_file_encoding = "utf-8"

settings = Settings()
