from database.user_db import User
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from jwt import decode as jwtDecode
from jwt import encode as jwtEncode
from passlib.context import CryptContext
from utils.env_util import gv

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthFailed(Exception):
    def __init__(self, error_type: str):
        self.error_type = error_type


def create_token(data: dict) -> str:
    token = jwtEncode(data, gv.SECRET_KEY, algorithm=gv.ALGORITHM)
    return token


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        jwt_data = jwtDecode(token, gv.SECRET_KEY, algorithms=[gv.ALGORITHM])
        if not await User.auth_user(jwt_data["user"], jwt_data["passwd"]):
            raise AuthFailed("凭证无效")

        return jwt_data

    except (PyJWTError, KeyError):
        raise AuthFailed("凭证无效")


async def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        jwt_data = jwtDecode(token, gv.SECRET_KEY, algorithms=[gv.ALGORITHM])
        if not await User.auth_user(jwt_data["user"], jwt_data["passwd"]):
            raise AuthFailed("凭证无效")

        if not await User.is_admin(jwt_data["user"]):
            raise AuthFailed("凭证无效")

        return jwt_data

    except (PyJWTError, KeyError):
        raise AuthFailed("凭证无效")
