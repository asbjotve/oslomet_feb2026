from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from config.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
FAST_TOKEN = settings.FASTAPI_TOKEN

def require_token(token: str = Depends(oauth2_scheme)):
    if token != FAST_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ugyldig eller manglende token",
            headers={"WWW-Authenticate": "Bearer"},
        )
