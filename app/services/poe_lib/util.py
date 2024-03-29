try:
    from ujson import dumps
except Exception:
    from json import dumps
from base64 import b64decode, b64encode
from os import path
from random import choice
from string import ascii_letters, digits
from time import localtime, strftime

SUB_HASH_PATH = path.join(path.dirname(path.abspath(__file__)), "sub_hash.json")
QUERY_HASH_PATH = path.join(path.dirname(path.abspath(__file__)), "query_hash.json")
GQL_URL = "https://poe.com/api/gql_POST"
SETTING_URL = "https://poe.com/api/settings"
MODEL_IMG_URL_CACHE = {
    "Assistant": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/assistant.b077c338.svg",
    "Claude-instant-100k": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/anthropicAvatarBeige.426c3b88.png",
    "GPT-4": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/openAIBlue.915c0399.png",
    "Claude-2-100k": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/anthropicAvatarBrown.e8c26390.png",
    "Claude-instant": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/anthropicAvatarBeige.426c3b88.png",
    "ChatGPT": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/chatGPTAvatar.04ed8443.png",
    "GPT-3.5-Turbo-Instruct": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/chatGPTAvatar.04ed8443.png",
    "GPT-3.5-Turbo": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/chatGPTAvatar.04ed8443.png",
    "Google-PaLM": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/googlePalmAvatar.5ca326b0.webp",
}


def generate_data(query_name: str, variables: dict, hash: str) -> str:
    data = {
        "queryName": query_name,
        "variables": variables,
        "extensions": {"hash": hash},
    }
    return dumps(data, separators=(",", ":"))


def generate_random_handle(c) -> str:
    """生成随机handle"""
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(c))


def base64_encode(text: str) -> str:
    return b64encode(text.encode("utf-8")).decode("utf-8")


def base64_decode(text: str) -> str:
    return b64decode(text).decode("utf-8")


def str_time(t: int) -> str:
    return strftime("%Y-%m-%d %H:%M:%S", localtime(t / 1000))
