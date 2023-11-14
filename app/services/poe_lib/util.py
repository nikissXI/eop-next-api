try:
    from ujson import dumps
except:
    from json import dumps
from random import choice
from string import ascii_letters, digits
from base64 import b64encode, b64decode
from time import localtime, strftime

QUERIES = {
    "settingsPageQuery": "6d3480bc9f0edc5470c755bc245593d120e8c3741d3b8448828d03015131055e",  # 获取账号信息
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",  # 订阅ws
    "exploreBotsIndexPageQuery": "96026f5201635559989830b63ec55dcf6080abe8152a52f39ffb98b46d6850d4",  # 探索某类bot
    "ExploreBotsListPaginationQuery": "91c2b3d288db2bd7018f954414a12123f745c243709b02a9216d575d2c0fe8c9",  # 查询具体类别bot列表
    "editBotIndexPageQuery": "e3ff9a95e121979be704ad7d2710e3f4dd590bae4aace961131a5f9f8cf22047",  # 获取自定义bot的资料 todo
    "EditBotMain_poeBotEdit_Mutation": "b4378a80d21017d3e3788945b7648f8164e699d69878e3384bbd5dc127f159e6",  # 编辑自定义bot
    "HandleBotLandingPageQuery": "7f06985a6204b906a804e8c597058106d1e9d4b305bf0cb95e3c50e5caaa88ac",  # 查询bot信息
    "sendMessageMutation": "645db20c90c19cbf3524a969912325cae0838f0e7a6422a623d06de0de7dcda8",  # 发送消息
    "sendChatBreakMutation": "62e344f18eb96c781f6560a42ef101287b3564b5d6acfb5190773342c71a043e",  # 重置记忆
    "createBotIndexPageQuery": "61134731fa4e4cc9b2006b6a819f343dc91876f91a6e1cd28d49826bba79e4e7",  # 创建自定义bot时可选的模型
    "CreateBotMain_poeBotCreate_Mutation": "384184cd2e904bb0da2ce55ad2b36fd320463e52572147f6663aa53be26cc8e7",  # 创建自定义bot
    "EditBotMain_poeBotEdit_Mutation": "b4378a80d21017d3e3788945b7648f8164e699d69878e3384bbd5dc127f159e6",  # 编辑自定义bot
    "BotInfoCardActionBar_poeBotDelete_Mutation": "b446d0e94980e36d9ba7a5bc3188850186069d529b4c337fb9e91b9ead876c12",  # 删除bot
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",  # 删除会话
    "ChatListPaginationQuery": "43d655f35f164654f7a04a577065e5dcd00ca68d235473a8d08872c330bc565c",  # 查询聊天记录
    "chatHelpers_messageCancel_Mutation": "33ae28dd801cbaeb3e988a9db5097b065329af60b99f6de710ffd1fae5ce995e",  # 取消回答
}
GQL_URL = "https://poe.com/api/gql_POST"
SETTING_URL = "https://poe.com/api/settings"
BOT_IMAGE_LINK_CACHE = {
    "Assistant": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/assistant.b077c338.svg",
    "Claude-instant-100k": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/anthropicAvatarBeige.426c3b88.png",
    "GPT-4": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/openAIBlue.915c0399.png",
    "Claude-2-100k": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/anthropicAvatarBrown.e8c26390.png",
    "Claude-instant": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/anthropicAvatarBeige.426c3b88.png",
    "ChatGPT": "https://psc2.cf2.poecdn.net/a5b9fd229f21a733a02fe04c2b9ccc3af7f8239b/_next/static/media/chatGPTAvatar.04ed8443.png",
    "GPT-3.5-Turbo-Instruct": "https://psc2.cf2.poecdn.net/a5b9fd229f21a733a02fe04c2b9ccc3af7f8239b/_next/static/media/chatGPTAvatar.04ed8443.png",
    "Google-PaLM": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/googlePalmAvatar.5ca326b0.webp",
}


def generate_data(query_name, variables) -> str:
    data = {
        "queryName": query_name,
        "variables": variables,
        "extensions": {"hash": QUERIES[query_name]},
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
