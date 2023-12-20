from os import getenv
from secrets import token_urlsafe

from dotenv import load_dotenv

try:
    from ujson import loads
except Exception:
    from json import loads


load_dotenv()

if _ := getenv("API_PATH"):
    API_PATH = _
else:
    API_PATH = ""

if _ := getenv("HOST"):
    HOST = _
else:
    HOST = "127.0.0.1"

if _ := getenv("PORT"):
    PORT = int(_)
else:
    PORT = 8080

if _ := getenv("ORIGINS"):
    ORIGINS = loads(_)
else:
    ORIGINS = ["*"]

SSL_KEYFILE_PATH = getenv("SSL_KEYFILE_PATH")
SSL_CERTFILE_PATH = getenv("SSL_CERTFILE_PATH")

if _ := getenv("SECRET_KEY"):
    SECRET_KEY = _
else:
    SECRET_KEY = token_urlsafe(32)

if _ := getenv("ALGORITHM"):
    ALGORITHM = _
else:
    ALGORITHM = "HS256"

if _ := getenv("UPLOAD_KEY"):
    UPLOAD_KEY = _
else:
    UPLOAD_KEY = "UPLOAD_KEY"
