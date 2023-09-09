from random import choice
from string import ascii_letters, digits
from hashlib import sha256
from logging import getLogger

logger = getLogger("uvicorn.error")


def generate_random_password(length=8) -> tuple[str, str]:
    characters = ascii_letters + digits
    passwd = "".join(choice(characters) for _ in range(length))
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    return passwd, hash_object.hexdigest()
