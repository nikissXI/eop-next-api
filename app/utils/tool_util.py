from hashlib import sha256
from logging import DEBUG, FileHandler, Formatter, getLogger
from random import choice
from string import ascii_letters, digits

from database.user_db import User

################
### 日志配置
################
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


user_logger = getLogger("user_action")
file_handler = FileHandler("user_action.log")
formatter = Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
user_logger.addHandler(file_handler)
user_logger.setLevel(DEBUG)


async def log_user_action(uid: int, msg: str, level: str = "info"):
    user_name = await User.get_username(uid)
    if level == "error":
        user_logger.error(f"用户:{user_name}  uid:{uid}  {msg}")
    else:
        user_logger.info(f"用户:{user_name}  uid:{uid}  {msg}")


# debug_logger = getLogger("debug_logger")
# file_handler = FileHandler("debug_logger.log")
# formatter = Formatter("%(asctime)s - %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")
# file_handler.setFormatter(formatter)
# debug_logger.addHandler(file_handler)
# debug_logger.setLevel(DEBUG)


def generate_random_password(length=8) -> tuple[str, str]:
    characters = ascii_letters + digits
    passwd = "".join(choice(characters) for _ in range(length))
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    return passwd, hash_object.hexdigest()
