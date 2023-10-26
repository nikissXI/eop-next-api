try:
    from ujson import dumps
except:
    from json import dumps
from random import choice
from string import ascii_letters, digits
from base64 import b64encode, b64decode
from time import localtime, strftime

QUERIES = {
    "BotInfoCardActionBar_poeBotDelete_Mutation": "b446d0e94980e36d9ba7a5bc3188850186069d529b4c337fb9e91b9ead876c12",  # 删除bot
    "chatHelpers_messageCancel_Mutation": "33ae28dd801cbaeb3e988a9db5097b065329af60b99f6de710ffd1fae5ce995e",  # 取消回答
    "ChatListPaginationQuery": "c91cc3bcb543ad7036d40125777d2374d7d0228ad6fc5b6f4683938141f0a6ad",  # 查询聊天记录
    "createBotIndexPageQuery": "1322f28e5102bfc8419a75ca118bf9fd697fe2cac6c61174b59605d056150fed",  # 创建自定义bot时可选的模型
    "CreateBotMain_poeBotCreate_Mutation": "bb796e46ed9e50e8d040d6e22a1471f6853991d01f852eb7eb594a8a6b85bcb7",  # 创建自定义bot
    "exploreBotsIndexPageQuery": "96026f5201635559989830b63ec55dcf6080abe8152a52f39ffb98b46d6850d4",  # 探索某类bot
    "editBotIndexPageQuery": "e3ff9a95e121979be704ad7d2710e3f4dd590bae4aace961131a5f9f8cf22047",  # 获取自定义bot的资料 todo
    "EditBotMain_poeBotEdit_Mutation": "b4378a80d21017d3e3788945b7648f8164e699d69878e3384bbd5dc127f159e6",  # 编辑自定义bot
    "ExploreBotsListPaginationQuery": "91c2b3d288db2bd7018f954414a12123f745c243709b02a9216d575d2c0fe8c9",  # 查询具体类别bot列表
    "HandleBotLandingPageQuery": "419ec9b64012509ef0e0f7180909b87f70124ba10a1c2c3d898522708ea4a236",  # 查询bot信息
    "sendChatBreakMutation": "62e344f18eb96c781f6560a42ef101287b3564b5d6acfb5190773342c71a043e",  # 重置记忆
    "sendMessageMutation": "2a3fda864652df1320f2e8d50576bf8bf85d1a78b130ecae98f1afd88c182608",  # 发送消息
    "settingsPageQuery": "7590b13df7602b9fbc393a67204b5e70d1e5630ac376fea0fd9aa678addd25aa",  # 获取账号信息
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",  # 订阅ws
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",  # 删除会话
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
    "ChatGPT": "比较出名以及常用的gpt-3.5-turbo模型，上下文支持约4k个词。",
    "ChatGPT-16k": "（该模型有使用次数限制）增强版ChatGPT，上下文支持约16k个词。",
    "GPT-4-32k": "（该模型有使用次数限制）增强版GPT-4，上下文支持约32k个词。",
    "Google-PaLM": "由PaLM2 chat-bison模型提供支持，上下文支持约8k个词。",
    "Llama-2-70b": "由Llama-2-70b-chat模型提供支持。",
    "Code-Llama-34b": "Code-Llama-34b-instruct模型。擅长生成和讨论代码，上下文支持约16k个词。",
    "Llama-2-13b": "由Llama-2-13b-chat模型提供支持。",
    "Llama-2-7b": "由Llama-2-7b-chat模型提供支持。",
    "Code-Llama-13b": "由Code-Llama-13b-instruct模型提供支持。擅长生成和讨论代码，上下文支持约16k个词。",
    "Code-Llama-7b": "由Code-Llama-7b-instruct模型提供支持。擅长生成和讨论代码，上下文支持约16k个词。",
    "Solar-0-70b": "Solar-0-70b-16bit是HuggingFace Open LLM排行榜上排名靠前的模型，是Llama 2的微调版本。",
    "GPT-3.5-Turbo-Instruct": "新的指令语言模型，旨在有效地提供特定指令，类似于专注于聊天的ChatGPT。",
    "Web-Search": "由ChatGPT模型提供支持。能够根据需要进行网络搜索以获取信息并提供回答。特别适用于与最新信息或具体事实相关的查询。",
    "GPT-3.5-Turbo": "ChatGPT，但没有系统默认prompt。",
    "StableDiffusionXL": "根据用户的提示生成高质量图像。用户可以使用提示末尾的“--no”参数指定图像中要避免的元素（例如：“Tall trees, daylight --no rain”）。",
    "fw-mistral-7b": "由Mistral-7b-instruct模型提供支持。官网地址：https://app.fireworks.ai/models/fireworks/mistral-7b-instruct-4k。",
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
