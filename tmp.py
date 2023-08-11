from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jwt import PyJWTError,encode as jwtEncode,decode as jwtDecode

app = FastAPI()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict) -> str:
    encoded_jwt = jwtEncode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        decoded_token = jwtDecode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    data = verify_token(token)
    return data


@app.get("/protected_route")
async def protected_route(current_user: dict = Depends(get_current_user)):
    # 在这里可以使用 current_user 对象进行身份验证后的操作
    return {"message": "Access granted"}