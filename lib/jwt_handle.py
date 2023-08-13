from secrets import token_urlsafe
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from jwt import decode as jwtDecode
from jwt import encode as jwtEncode
from passlib.context import CryptContext

# SECRET_KEY = token_urlsafe(32)
SECRET_KEY = "test_key_you_know"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: dict) -> str:
    token = jwtEncode(data, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> dict:
    try:
        jwt_data = jwtDecode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return jwt_data
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    data = verify_token(token)
    return data
