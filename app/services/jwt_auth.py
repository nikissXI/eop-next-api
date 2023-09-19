from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from jwt import decode as jwtDecode
from jwt import encode as jwtEncode
from passlib.context import CryptContext
from utils.config import *
from database import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthFailed(Exception):
    def __init__(self, error_type: str):
        self.error_type = error_type


def create_token(data: dict) -> str:
    token = jwtEncode(data, SECRET_KEY, algorithm=ALGORITHM)
    return token


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        jwt_data = jwtDecode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return jwt_data

    except PyJWTError:
        raise AuthFailed("凭证无效")


async def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        jwt_data = jwtDecode(token, SECRET_KEY, algorithms=[ALGORITHM])
        level = await User.get_level(jwt_data["user"])
        if level != 0:
            raise AuthFailed("权限不足")
        return jwt_data

    except PyJWTError:
        raise AuthFailed("凭证无效")
