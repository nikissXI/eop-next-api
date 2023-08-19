from random import choice
from string import ascii_letters, digits
from logging import getLogger
from hashlib import sha256

logger = getLogger("uvicorn.error")


def generate_random_bot_id() -> str:
    """生成随机字符串"""
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(20))


def generate_random_password(length=8) -> tuple[str, str]:
    characters = ascii_letters + digits
    passwd = "".join(choice(characters) for _ in range(length))
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    return passwd, hash_object.hexdigest()
