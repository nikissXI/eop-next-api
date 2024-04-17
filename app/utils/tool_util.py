from hashlib import sha256
from logging import DEBUG, FileHandler, Formatter, getLogger
from random import choice
from string import ascii_letters, digits

from database.user_db import User

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
