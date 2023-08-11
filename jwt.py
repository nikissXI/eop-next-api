from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jwt import PyJWTError, encode as jwtEncode, decode as jwtDecode
from fastapi import Depends, HTTPException
from secrets import token_urlsafe

SECRET_KEY = token_urlsafe(32)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict) -> str:
    encoded_jwt = jwtEncode(data, SECRET_KEY)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        decoded_token = jwtDecode(token, SECRET_KEY)
        return decoded_token
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    data = verify_token(token)
    return data
