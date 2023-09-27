try:
    from ujson import dumps
except:
    from json import dumps
from random import choice
from string import ascii_letters, digits
from base64 import b64encode, b64decode
from time import localtime, strftime

QUERIES = {
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",  # 订阅ws
    "exploreBotsIndexPageQuery": "b6b0fb768c7727b57f4cb51489a3850ded36d1b96e27c1346f04171db0b2cf25",  # 探索某类bot
    "ExploreBotsListPaginationQuery": "983be13fda71b7926b77f461ae7e8925c4e696cdd578fbfd42cb0d14103993ac",  # 查询具体类别bot列表
    "createBotIndexPageQuery": "3925692460e7c12565a722f1f934620ff5190c6023b80c86c7529159953ef73c",  # 创建自定义bot时可选的模型
    "HandleBotLandingPageQuery": "9f8049fbcbd162ac0121cee1014290c81671673fa2466b4ebd14e33c4f8e155f",  # 查询bot信息
    "sendMessageMutation": "f7887d68040b45a71d92c46b067fd88539d5d4a51dd9102bde3a4f4fe109bc56",  # 发送消息
    "sendChatBreakMutation": "f392431130dd344ef7ca7409699ebb312a12f581a046a403f26c2657101f7fce",  # 重置记忆
    "BotInfoCardActionBar_poeBotDelete_Mutation": "08da8a2ff41d15ccd6da7488e1c5ae94101c6037f84505845f43c3526de315f9",  # 删除bot
    "CreateBotMain_poeBotCreate_Mutation": "916833ab4558f9afbfdf8e7f181514dda8ab2f77e07a7ef6a6cb75ea83c41e6e",  # 创建bot
    "EditBotMain_poeBotEdit_Mutation": "7a04278f837f1c61321e35b70513166fc8bf93d7f551eaa6a6675774ea190a25",  # 编辑自定义bot
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",  # 删除会话
    "ChatListPaginationQuery": "81d85f26b14aa782bef3ef617ce2222453f3b6ebc4dfaa1b50470a2fb157b58a",  # 查询聊天记录
    "chatHelpers_messageCancel_Mutation": "59b10f19930cf95d3120612e72d271e3346a7fc9599e47183a593a05b68c617e",  # 取消回答
    "settingsPageQuery": "faa6a828e2da41a3212827437562536671ab50d99e825e8399b649668ec1652a",  # 获取账号信息
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
CHINESE_DISCRIPTION = {
    "Assistant": "由ChatGPT模型提供支持。旧名Sage。擅长编程相关和科学逻辑相关任务，思维方式更接近人类。",
    "Claude-instant-100k": "（该模型有使用次数限制）可分析非常长的文档、代码等，上下文支持约75k个词。",
    "GPT-4": "（该模型有使用次数限制）在定量问题（数学和物理）、创意写作和许多其他具有挑战性的任务方面比ChatGPT更强大。上下文支持约8k个词。",
    "Claude-2-100k": "（该模型有使用次数限制）特别擅长创意写作，上下文支持约75k个词。",
    "Claude-instant": "擅长创意任务，上下文支持约7k个词。",
    "ChatGPT": "比较出名以及常用的模型，上下文支持约4k个词。",
    "ChatGPT-16k": "（该模型有使用次数限制）增强版ChatGPT，上下文支持约16k个词。",
    "GPT-4-32k": "（该模型有使用次数限制）增强版GPT-4，上下文支持约32k个词。",
    "Google-PaLM": "由PaLM2 chat-bison模型提供支持，上下文支持约8k个词。",
    "Llama-2-70b": "Llama-2-70b-chat模型。",
    "Code-Llama-34b": "Code-Llama-34b-instruct模型。擅长生成和讨论代码，上下文支持约16k个词。",
    "Llama-2-13b": "Llama-2-13b-chat模型。",
    "Llama-2-7b": "Llama-2-7b-chat模型。",
    "Code-Llama-13b": "Code-Llama-13b-instruct。擅长生成和讨论代码，上下文支持约16k个词。",
    "Code-Llama-7b": "Code-Llama-7b-instruct。擅长生成和讨论代码，上下文支持约16k个词。",
    "Solar-0-70b": "Solar-0-70b-16bit是HuggingFace Open LLM排行榜上排名靠前的模型，是Llama 2的微调版本。",
    "GPT-3.5-Turbo-Instruct": "新的指令语言模型，旨在有效地提供特定指令，类似于专注于聊天的ChatGPT。",
    "Web-Search": "由ChatGPT模型提供支持。能够根据需要进行网络搜索以获取信息并提供回答。特别适用于与最新信息或具体事实相关的查询。",
}


def generate_data(query_name, variables) -> str:
    data = {
        "queryName": query_name,
        "variables": variables,
        "extensions": {"hash": QUERIES[query_name]},
    }
    return dumps(data, separators=(",", ":"))


def generate_random_handle() -> str:
    """生成随机handle"""
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(20))


def base64_encode(text: str) -> str:
    return b64encode(text.encode("utf-8")).decode("utf-8")


def base64_decode(text: str) -> str:
    return b64decode(text).decode("utf-8")


def str_time(t: int) -> str:
    return strftime("%Y-%m-%d %H:%M:%S", localtime(t / 1000))
