from asyncio import run, sleep
from hashlib import md5
from random import randint

from httpx import AsyncClient
from loguru import logger
from ujson import dumps, loads

query_hash = {
    "BotInfoCardActionBar_poeBotDelete_Mutation": "4fc0ad086150c4b3fb94d9fefb9589cd54fe5a10eb37ea55af9161045e99df53",
    "createBotIndexPageQuery": "5de821b416154f7d3dbb6ca4cab5c20277df0c968e6b80a950a14446c7b91b9f",
    "ChatListPaginationQuery": "2fd60cc5b28241d66ffcb89f6447f67c6c4fc0ee21bb4d9ec3b6b37c3caa60a3",
    "CreateBotMain_poeBotCreate_Mutation": "d7df8a85d7b0fd14899bb7571cb36b1a6079a91eef84ff65f7b29850113a6582",
    "exploreBotsIndexPageQuery": "5e0b7b84186d9520510a584622616be9556e9feee8a1202f9a9ddfcdd58684ec",
    "EditBotMain_poeBotEdit_Mutation": "05b15342e3c39bfdfb9f9e9281f30f3aa6e78a37f4f0dd3741f29a9afd67e99d",
    "ExploreBotsListPaginationQuery": "cd11a0b3a4c42de7ef3d3a1467ff88ba92cea650da986479e42fb960ad25504a",
    "HandleBotLandingPageQuery": "8bbeb3be35326a0fd36afa85bbf7af72d5a5264c1ffa6868bf1b0af27bb29ffe",
    "regenerateMessageMutation": "056f5f4b6a39ca7786a4f0b2ef37eee401c81d6086cd78ffc12fe2ce0bccb1fd",
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",
    "settingsPageQuery": "65b051752fda1e755c0b0e8ff45a95ee8a71bbc31a307ae5fa865e8af1004cae",
    "sendMessageMutation": "0ca282da57c815e944c834778569be6bfc99ae1a08686e1e521c4ac09a3b5540",
    "sendChatBreakMutation": "8f4404376f27cc590b0026a3280a8bc15339bd86f05fa85a1f53b483e5c30ce4",
    "stopMessage_messageCancel_Mutation": "ddf2377e985684709863d9c10d83d127a0ee7bb92b2ffbde610285b0181141ab",
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",
}
formkey = "255244e838988db50646964f4732b5bc"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cookie": "p-b=mYD8V4SgcKBbVqmqf_TStg%3D%3D; p-lat=m87QpzTePBejSqgfcfxonJTrY7YSQZ40dyWrO53FfQ%3D%3D",
    "Poe-Formkey": formkey,
    # "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
    "Sec-Ch-Ua": '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
    "Origin": "https://poe.com",
    "Referer": "https://poe.com/settings",
}
httpx_client = AsyncClient(headers=headers, proxies="http://127.0.0.1")


def generate_data(query_name: str, variables: dict, hash: str) -> str:
    data = {
        "queryName": query_name,
        "variables": variables,
        "extensions": {"hash": hash},
    }
    return dumps(data, separators=(",", ":"))


async def send_query(query_name: str, variables: dict):
    """
    发送请求
    """

    data = generate_data(query_name, variables, query_hash[query_name])
    base_string = data + formkey + "4LxgHM6KpFqokX0Ox"
    resp = await httpx_client.post(
        "https://poe.com/api/gql_POST",
        content=data,
        headers={
            "content-type": "application/json",
            "poe-tag-id": md5(base_string.encode()).hexdigest(),
        },
        timeout=10,
    )

    print(resp.status_code)
    json_data = loads(resp.text)
    print(json_data)


async def main():
    await send_query("settingsPageQuery", {})


run(main())
