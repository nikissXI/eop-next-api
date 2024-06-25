################
### 日志配置
################
import logging
from hashlib import sha256
from logging import DEBUG, FileHandler, Formatter, StreamHandler, getLogger
from random import choice
from string import ascii_letters, digits

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

fastapi_logger_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(levelprefix)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file_default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(levelprefix)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
        "file_access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file_default": {
            "formatter": "file_default",
            "class": "logging.FileHandler",
            "filename": "./server.log",
        },
        "file_access": {
            "formatter": "file_access",
            "class": "logging.FileHandler",
            "filename": "./server.log",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default", "file_default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {
            "handlers": ["access", "file_access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
logger = getLogger("uvicorn.error")


class Filter404(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "404" not in record.getMessage()


# Apply the custom filter to Uvicorn's access logger
logging.getLogger("uvicorn.access").addFilter(Filter404())


class Custom404Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if response.status_code == 404:
            # Prevent logging for 404 responses
            return Response(status_code=404)
        return response


user_action = getLogger("user_action")
file_handler = FileHandler("user_action.log")
# formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
formatter = Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
user_action.addHandler(file_handler)
user_action.setLevel(DEBUG)


debug_logger = getLogger("debug_logger")
file_handler = FileHandler("debug_logger.log")
formatter = Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
debug_logger.addHandler(file_handler)
debug_logger.setLevel(DEBUG)


def generate_random_password(length=16) -> tuple[str, str]:
    characters = ascii_letters + digits
    passwd = "".join(choice(characters) for _ in range(length))
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    return passwd, hash_object.hexdigest()
