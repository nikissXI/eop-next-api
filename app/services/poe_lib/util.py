from base64 import b64decode, b64encode
from os import path
from random import choice
from string import ascii_letters, digits
from time import localtime, strftime

from ujson import dumps
from utils.tool_util import logger

SUB_HASH_PATH = path.join(path.dirname(path.abspath(__file__)), "sub_hash.json")
QUERY_HASH_PATH = path.join(path.dirname(path.abspath(__file__)), "query_hash.json")
GQL_URL = "https://poe.com/api/gql_POST"
GQL_URL_FILE = "https://poe.com/api/gql_upload_POST"
SETTING_URL = "https://poe.com/api/settings"
IMG_URL_CACHE = {
    "Assistant": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/assistant.b077c338.svg",
    "Claude-instant-100k": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/anthropicAvatarBeige.426c3b88.png",
    "GPT-4": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/openAIBlue.915c0399.png",
    "Claude-2-100k": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/anthropicAvatarBrown.e8c26390.png",
    "Claude-instant": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/anthropicAvatarBeige.426c3b88.png",
    "ChatGPT": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/chatGPTAvatar.04ed8443.png",
    "GPT-3.5-Turbo-Instruct": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/chatGPTAvatar.04ed8443.png",
    "GPT-3.5-Turbo": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/chatGPTAvatar.04ed8443.png",
    "Google-PaLM": "https://psc2.cf2.poecdn.net/e42c69ddd5cee63fde977757d950352e3ea081b9/_next/static/media/googlePalmAvatar.5ca326b0.webp",
    "null": "https://psc2.cf2.poecdn.net/assets/_next/static/media/defaultAvatar.7e5c73d2.png",
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


def get_img_url(botName: str, img_info: dict | None) -> str:
    if img_info is None:
        img_url = IMG_URL_CACHE["null"]

    elif img_info["__typename"] == "URLBotImage":
        img_url = img_info["url"]

    elif botName in IMG_URL_CACHE:
        img_url = IMG_URL_CACHE[botName]

    else:
        logger.warning(f"{botName}找不到头像链接")
        img_url = IMG_URL_CACHE["null"]

    return img_url


def filter_bot_result(_edges: list) -> list[dict[str, str]]:
    bots: list[dict] = []
    for _edge in _edges:
        # 名称
        botName = _edge["node"]["displayName"]
        # 头像链接
        img_url = get_img_url(botName, _edge["node"]["picture"])
        # 描述
        description = _edge["node"]["description"].replace("\n", "")
        # 类型
        bot_type = "官方" if "官方" in _edge["node"]["translatedBotTags"] else "第三方"
        # 月活用户，官方bot为null
        monthly_active = _edge["node"]["monthlyActiveUsers"]

        bots.append(
            {
                "name": botName,
                "imgUrl": img_url,
                "description": description,
                "botType": bot_type,
                "monthlyActive": monthly_active,
            }
        )

    return bots


def filter_bot_info(_bot_info: dict) -> dict:
    if "isOfficialBot" in _bot_info:
        if _bot_info["isOfficialBot"]:
            bot_type = "官方"
        elif _bot_info["isPrivateBot"]:
            bot_type = "自定义"
        else:
            bot_type = "第三方"
    else:
        if "OFFICIAL" in _bot_info["translatedBotTags"]:
            bot_type = "官方"
        else:
            bot_type = "第三方"

    img_url = get_img_url(_bot_info["displayName"], _bot_info["picture"])

    bot_info = {
        "botName": _bot_info["displayName"],
        "botId": _bot_info["botId"],
        "botHandle": _bot_info["nickname"],
        "description": _bot_info["description"] if "description" in _bot_info else "",
        "allowImage": _bot_info["allowsImageAttachments"],
        "allowFile": _bot_info["supportsFileUpload"],
        "uploadFileSizeLimit": _bot_info["uploadFileSizeLimit"],
        "imgUrl": img_url,
        "price": _bot_info["messagePointLimit"]["displayMessagePointPrice"],
        "botType": bot_type,
        "canAccess": _bot_info["canUserAccessBot"],
    }
    return bot_info


def filter_basic_bot_info(_bot_list: list) -> list[dict]:
    bot_list = []
    for _bot_info in _bot_list:
        img_url = get_img_url(_bot_info["displayName"], _bot_info["picture"])
        bot_list.append(
            {
                "botName": _bot_info["displayName"],
                "imgUrl": img_url,
                "botId": _bot_info["botId"],
                "model": _bot_info["model"],
                "isImageGen": _bot_info["isImageGen"],
                "isVideoGen": _bot_info["isVideoGen"],
            }
        )
    return bot_list
