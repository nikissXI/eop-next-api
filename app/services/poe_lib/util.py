try:
    from ujson import dumps
except:
    from json import dumps
from random import choice
from string import ascii_letters, digits
from base64 import b64encode, b64decode

QUERIES = {
    "exploreBotsIndexPageQuery": "b6b0fb768c7727b57f4cb51489a3850ded36d1b96e27c1346f04171db0b2cf25",  #
    "ExploreBotsListPaginationQuery": "983be13fda71b7926b77f461ae7e8925c4e696cdd578fbfd42cb0d14103993ac",  #
    "createBotIndexPageQuery": "3925692460e7c12565a722f1f934620ff5190c6023b80c86c7529159953ef73c",  #
    "HandleBotLandingPageQuery": "9f8049fbcbd162ac0121cee1014290c81671673fa2466b4ebd14e33c4f8e155f",  # 
    "sendMessageMutation": "d5be9015e04fe40923c598bc44b4849eee161e284b243cad6de48eaf5f0f6e22",  #
    "sendChatBreakMutation": "f392431130dd344ef7ca7409699ebb312a12f581a046a403f26c2657101f7fce",  #
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",  #
    "BotInfoCardActionBar_poeBotDelete_Mutation": "08da8a2ff41d15ccd6da7488e1c5ae94101c6037f84505845f43c3526de315f9",  #
    "CreateBotMain_poeBotCreate_Mutation": "916833ab4558f9afbfdf8e7f181514dda8ab2f77e07a7ef6a6cb75ea83c41e6e",  #
    "EditBotMain_poeBotEdit_Mutation": "7a04278f837f1c61321e35b70513166fc8bf93d7f551eaa6a6675774ea190a25",  #
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",  #
    "ChatListPaginationQuery": "81d85f26b14aa782bef3ef617ce2222453f3b6ebc4dfaa1b50470a2fb157b58a",  #
    "chatHelpers_messageCancel_Mutation": "59b10f19930cf95d3120612e72d271e3346a7fc9599e47183a593a05b68c617e",  #
    "settingsPageQuery": "d81f0e97947680bef2fb6e0ac5947e9198b613575010351995ab565f9ae59cad",  #
}
GQL_URL = "https://poe.com/api/gql_POST"
SETTING_URL = (
    "https://poe.com/api/settings?channel=poe-chan52-8888-iimnqpoozcytkitfqkud"
)


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
