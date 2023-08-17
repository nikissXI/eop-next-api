from dotenv import load_dotenv
from os import getenv
from secrets import token_urlsafe

load_dotenv()

if _ := getenv("API_PATH"):
    API_PATH = _
else:
    API_PATH = "/api"

if _ := getenv("HOST"):
    HOST = _
else:
    HOST = "127.0.0.1"

if _ := getenv("PORT"):
    PORT = int(_)
else:
    PORT = 8080

SSL_KEYFILE_PATH = getenv("SSL_KEYFILE_PATH")
SSL_CERTFILE_PATH = getenv("SSL_CERTFILE_PATH")
ADMIN_USERNAME = getenv("ADMIN_USERNAME")

if _ := getenv("SECRET_KEY"):
    SECRET_KEY = _
else:
    SECRET_KEY = token_urlsafe(32)

if _ := getenv("ALGORITHM"):
    ALGORITHM = _
else:
    ALGORITHM = "HS256"
