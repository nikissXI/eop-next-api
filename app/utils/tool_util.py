from random import choice
from string import ascii_letters, digits
from hashlib import sha256
from logging import getLogger, FileHandler, Formatter, DEBUG

logger = getLogger("uvicorn.error")

user_logger = getLogger("user_action")
file_handler = FileHandler("user_action.log")
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
user_logger.addHandler(file_handler)
user_logger.setLevel(DEBUG)


def generate_random_password(length=8) -> tuple[str, str]:
    characters = ascii_letters + digits
    passwd = "".join(choice(characters) for _ in range(length))
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    return passwd, hash_object.hexdigest()
