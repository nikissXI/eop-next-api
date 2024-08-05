from secrets import token_urlsafe

from pydantic_settings import BaseSettings, SettingsConfigDict


class Global_env(BaseSettings):
    model_config = SettingsConfigDict(env_file="config.txt", env_file_encoding="utf-8")

    API_PATH: str = "/"
    HOST: str = "127.0.0.1"
    PORT: int = 80
    LOG_LEVEL: str = "INFO"
    ORIGINS: list[str] = ["*"]
    SSL_KEYFILE_PATH: str | None = None
    SSL_CERTFILE_PATH: str | None = None
    SECRET_KEY: str = token_urlsafe(32)
    ALGORITHM: str = "HS256"
    UPLOAD_KEY: str = "ABCABCabcabc*&*&"


gv = Global_env()
