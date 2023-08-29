try:
    from ujson import dumps
except:
    from json import dumps
from random import choice
from string import ascii_letters, digits
from base64 import b64encode, b64decode

QUERIES = {
    "chatHelpersSendNewChatMessageMutation": "35efaf6ca1dc0cde7493491734e376472f31a889dba58357e965a29fbca17c93",
    "chatHelpers_sendMessageMutation_Mutation": "423f47cbc3c55eaeaa17b78c005e72cefc3dcf2bf1b107c4809828155046ab15",
    "chatHelpers_addMessageBreakEdgeMutation_Mutation": "9450e06185f46531eca3e650c26fa8524f876924d1a8e9a3fb322305044bdac3",
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",
    "BotInfoCardActionBar_poeBotDelete_Mutation": "08da8a2ff41d15ccd6da7488e1c5ae94101c6037f84505845f43c3526de315f9",
    "CreateBotMain_poeBotCreate_Mutation": "916833ab4558f9afbfdf8e7f181514dda8ab2f77e07a7ef6a6cb75ea83c41e6e",
    "EditBotMain_poeBotEdit_Mutation": "7a04278f837f1c61321e35b70513166fc8bf93d7f551eaa6a6675774ea190a25",
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",
    "ChatListPaginationQuery": "52e2f67bbb09cd74ab7300610e0b6cf1e6626fdbe8bcd8f88a3064d88c6dfac0",
    "chatHelpers_messageCancel_Mutation": "59b10f19930cf95d3120612e72d271e3346a7fc9599e47183a593a05b68c617e",
    "settingsPageQuery": "6f9bb5afab6d0b1cad62d49a0cbe724177a2880299388f09230b70d8850664b2",
}
GQL_URL = "https://poe.com/api/gql_POST"
SETTING_URL = "https://poe.com/api/settings"


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


# 显示名称：模型名称，描述，是否允许diy(使用prompt)，是否有限使用，botId
available_models: dict[str, tuple[str, str, bool, bool, int]] = {
    "ChatGPT": (
        "chinchilla",
        "由gpt-3.5-turbo驱动。",
        True,
        False,
        3004,
    ),
    "GPT-4": (
        "beaver",
        "OpenAI最强大的模型。在定量问题（数学和物理）、创造性写作和许多其他具有挑战性的任务方面比ChatGPT更强大。",
        True,
        True,
        3007,
    ),
    "Claude-instant": (
        "a2",
        "Anthropic的最快模型，在创造性任务方面表现出色。具有约7,000个单词的上下文窗口。",
        True,
        False,
        1006,
    ),
    "Claude-2-100k": (
        "a2_2",
        "Anthropic的最强大模型，其上下文窗口增加到约75,000个单词。在创意写作方面特别出色。",
        True,
        True,
        1008,
    ),
    "Assistant": (
        "capybara",
        "通用助手机器人，擅长处理编程相关任务和非英语语言。由gpt-3.5-turbo驱动。之前被称为Sage。",
        False,
        False,
        3002,
    ),
    "ChatGPT-16k": (
        "agouti",
        "由gpt-3.5-turbo-16k驱动。",
        False,
        True,
        3009,
    ),
    "GPT-4-32k": (
        "vizcacha",
        "由gpt-4-32k驱动。",
        False,
        True,
        3010,
    ),
    "Claude-instant-100k": (
        "a2_100k",
        "Anthropic的最快模型，具有增加到约75,000个单词的上下文窗口。能够分析非常长的文档、代码等内容。",
        False,
        True,
        1009,
    ),
    "Google-PaLM": (
        "acouchy",
        "由Google的PaLM 2 chat-bison-001模型驱动。",
        False,
        False,
        6000,
    ),
    "Llama-2-7b": (
        "llama_2_7b_chat",
        "来自Meta的Llama-2-7b-chat模型。",
        False,
        False,
        7002,
    ),
    "Llama-2-13b": (
        "llama_2_13b_chat",
        "来自Meta的Llama-2-13b-chat模型。",
        False,
        False,
        7001,
    ),
    "Llama-2-70b": (
        "llama_2_70b_chat",
        "来自Meta的Llama-2-70b-chat模型。",
        False,
        False,
        7000,
    ),
}
