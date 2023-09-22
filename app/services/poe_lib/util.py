try:
    from ujson import dumps
except:
    from json import dumps
from random import choice
from string import ascii_letters, digits
from base64 import b64encode, b64decode

QUERIES = {
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",  # 订阅ws
    "exploreBotsIndexPageQuery": "b6b0fb768c7727b57f4cb51489a3850ded36d1b96e27c1346f04171db0b2cf25",  #
    "ExploreBotsListPaginationQuery": "983be13fda71b7926b77f461ae7e8925c4e696cdd578fbfd42cb0d14103993ac",  #
    "createBotIndexPageQuery": "3925692460e7c12565a722f1f934620ff5190c6023b80c86c7529159953ef73c",  #
    "HandleBotLandingPageQuery": "9f8049fbcbd162ac0121cee1014290c81671673fa2466b4ebd14e33c4f8e155f",  #
    "sendMessageMutation": "f7887d68040b45a71d92c46b067fd88539d5d4a51dd9102bde3a4f4fe109bc56",  # 发送消息
    "sendChatBreakMutation": "f392431130dd344ef7ca7409699ebb312a12f581a046a403f26c2657101f7fce",  #
    "BotInfoCardActionBar_poeBotDelete_Mutation": "08da8a2ff41d15ccd6da7488e1c5ae94101c6037f84505845f43c3526de315f9",  #
    "CreateBotMain_poeBotCreate_Mutation": "916833ab4558f9afbfdf8e7f181514dda8ab2f77e07a7ef6a6cb75ea83c41e6e",  #
    "EditBotMain_poeBotEdit_Mutation": "7a04278f837f1c61321e35b70513166fc8bf93d7f551eaa6a6675774ea190a25",  #
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",  #
    "ChatListPaginationQuery": "81d85f26b14aa782bef3ef617ce2222453f3b6ebc4dfaa1b50470a2fb157b58a",  #
    "chatHelpers_messageCancel_Mutation": "59b10f19930cf95d3120612e72d271e3346a7fc9599e47183a593a05b68c617e",  # 取消回答
    "settingsPageQuery": "d81f0e97947680bef2fb6e0ac5947e9198b613575010351995ab565f9ae59cad",  #
}
GQL_URL = "https://poe.com/api/gql_POST"
SETTING_URL = "https://poe.com/api/settings"
BOT_IMAGE_LINK_CACHE = {
    "Assistant": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/assistant.b077c338.svg",  #
    "Claude-instant-100k": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/anthropicAvatarBeige.426c3b88.png",  #
    "GPT-4": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/openAIBlue.915c0399.png",  #
    "Claude-2-100k": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/anthropicAvatarBrown.e8c26390.png",  #
    "Claude-instant": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/anthropicAvatarBeige.426c3b88.png",  #
    "ChatGPT": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/chatGPTAvatar.04ed8443.png",  #
    "Google-PaLM": "https://psc2.cf2.poecdn.net/fab9eff39d9103cb5b73c37c950df83de29d8cf8/_next/static/media/googlePalmAvatar.5ca326b0.webp",  #
}
CHINESE_DISCRIPTION = {
    "Assistant": "通用助手机器人，擅长编程相关任务和非英语语言。由 gpt-3.5-turbo 提供支持。曾被称为 Sage。",
    "Claude-instant-100k": "Anthropic 最快的模型，具有增加的上下文窗口，可容纳 100k 个标记（约 75,000 个词）。可分析非常长的文档、代码等。",
    "GPT-4": "OpenAI 最强大的模型。在定量问题（数学和物理）、创意写作和许多其他具有挑战性的任务方面比 ChatGPT 更强大。目前可用性有限。",
    "Claude-2-100k": "Anthropic 最强大的模型，具有增加的上下文窗口，可容纳 100k 个标记（约 75,000 个词）。特别擅长创意写作。",
    "Claude-instant": "Anthropic 最快的模型，擅长创意任务。具有 9k 个标记的上下文窗口（约 7,000 个词）。",
    "ChatGPT": "由 gpt-3.5-turbo 提供支持。",
    "ChatGPT-16k": "由 gpt-3.5-turbo-16k 提供支持。由于这是一个测试版模型，使用限制可能会发生变化。",
    "GPT-4-32k": "由 gpt-4-32k 提供支持。由于这是一个测试版模型，使用限制可能会发生变化。",
    "Google-PaLM": "由 Google 的 PaLM 2 chat-bison 模型提供支持。支持 8k 个标记的上下文窗口。",
    "Llama-2-70b": "Meta 的 Llama-2-70b-chat。",
    "Code-Llama-34b": "Meta 的 Code-Llama-34b-instruct。擅长生成和讨论代码，并支持 16k 个标记的上下文窗口。",
    "Llama-2-13b": "Meta 的 Llama-2-13b-chat。",
    "Llama-2-7b": "Meta 的 Llama-2-7b-chat。",
    "Code-Llama-13b": "Meta 的 Code-Llama-13b-instruct。擅长生成和讨论代码，并支持 16k 个标记的上下文窗口。",
    "Code-Llama-7b": "Meta 的 Code-Llama-7b-instruct。擅长生成和讨论代码，并支持 16k 个标记的上下文窗口。",
    "Solar-0-70b": "Upstage 的 Solar-0-70b-16bit 是 HuggingFace Open LLM 排行榜上排名靠前的模型，是 Llama 2 的微调版本。",
    "GPT-3.5-Turbo-Instruct": "由 gpt-3.5-turbo-instruct 提供支持",
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
