from asyncio import create_task, sleep, Queue
from hashlib import md5
from secrets import token_hex
from httpx import AsyncClient
from traceback import format_exc

try:
    from ujson import loads, dump
except:
    from json import loads, dump
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed as ws_ConnectionClosed
from random import randint
from re import search
from time import time
from typing import AsyncGenerator, Tuple
from uuid import uuid5
from .type import *
from .util import (
    CONST_NAMESPACE,
    GQL_URL,
    HOME_URL,
    SETTING_URL,
    generate_data,
    generate_random_handle,
    base64_encode,
    base64_decode,
    available_models,
)

try:
    from utils import logger
except:
    from loguru import logger


class Poe_Client:
    def __init__(self, p_b: str, formkey: str, proxy: str | None = None):
        self.channel_url: str = ""
        self.bots: dict = {}
        self.formkey: str = formkey
        self.p_b: str = p_b
        self.sdid: str = ""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cookie": f"p-b={self.p_b}",
            "Poe-Formkey": self.formkey,
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        }
        self.httpx_client = AsyncClient(headers=headers, proxies=proxy)
        self.ws_client_task = None
        self.answer_queue: dict[int, Queue] = {}
        self.talking = False
        self.refresh_channel_time = time()
        self.refresh_channel_lock = False
        self.cache_answer_msg_id = {}

    async def login(self):
        """
        创建poe请求实例，可用于验证凭证是否有效。预加载可获取所有bot的基础数据
        """
        if not (self.p_b and self.formkey):
            raise Exception(f"p_b和formkey未正确填写，不登陆")

        logger.info("Poe登陆中。。。。。。")
        try:
            resp = await self.httpx_client.get(HOME_URL, timeout=3)

            json_data = search(
                r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>',
                resp.text,
            )
            if json_data is None:
                raise Exception("__NEXT_DATA__搜索结果为空")

            next_data = loads(json_data.group(1))

            self.sdid = str(
                uuid5(
                    CONST_NAMESPACE,
                    next_data["props"]["initialData"]["data"]["pageQuery"]["viewer"][
                        "poeUser"
                    ]["id"],
                )
            )
        except Exception as e:
            raise Exception(f"登陆失败，错误信息：{e}")

        self.ws_client_task = create_task(self.connect_to_channel())

        logger.info("Poe登陆成功！")
        return self

    async def refresh_channel_data(self):
        """
        此函数从设置_URL获取通道数据，获取tchannel_data，对话用的
        """
        try:
            resp = await self.httpx_client.get(SETTING_URL)
            json_data = loads(resp.text)

            tchannel_data = json_data["tchannelData"]
            self.httpx_client.headers["Poe-Tchannel"] = tchannel_data["channel"]
            ws_domain = f"tch{randint(1, int(1e6))}"[:8]
            self.channel_url = f'wss://{ws_domain}.tch.{tchannel_data["baseHost"]}/up/{tchannel_data["boxName"]}/updates?min_seq={tchannel_data["minSeq"]}&channel={tchannel_data["channel"]}&hash={tchannel_data["channelHash"]}'
        except Exception as e:
            err_msg = f"获取channel data失败，错误信息：{e}"
            logger.error(err_msg)
            raise Exception(err_msg)

        try:
            await self.send_query(
                "subscriptionsMutation",
                {
                    "subscriptions": [
                        {
                            "subscriptionName": "messageAdded",
                            "query": None,
                            "queryHash": "6d5ff500e4390c7a4ee7eeed01cfa317f326c781decb8523223dd2e7f33d3698",
                        },
                        {
                            "subscriptionName": "messageCancelled",
                            "query": None,
                            "queryHash": "dfcedd9e0304629c22929725ff6544e1cb32c8f20b0c3fd54d966103ccbcf9d3",
                        },
                        {
                            "subscriptionName": "messageDeleted",
                            "query": None,
                            "queryHash": "91f1ea046d2f3e21dabb3131898ec3c597cb879aa270ad780e8fdd687cde02a3",
                        },
                        {
                            "subscriptionName": "viewerStateUpdated",
                            "query": None,
                            "queryHash": "ee640951b5670b559d00b6928e20e4ac29e33d225237f5bdfcb043155f16ef54",
                        },
                        {
                            "subscriptionName": "messageLimitUpdated",
                            "query": None,
                            "queryHash": "d862b8febb4c058d8ad513a7c118952ad9095c4ec0a5471540133fc0a9bd3797",
                        },
                        {
                            "subscriptionName": "chatTitleUpdated",
                            "query": None,
                            "queryHash": "740e2c7ab27297b7a8acde39a400b932c71beb7e9b525280fc99c1639f1be93a",
                        },
                    ]
                },
            )
        except Exception as e:
            raise Exception(f"subscribe执行失败，错误信息：{e}")

    async def get_answer(self, data: dict):
        msg_list: list[dict] = [
            loads(msg_str) for msg_str in data.get("messages", "{}")
        ]
        for msg in msg_list:
            payload = msg.get("payload", {})

            if payload.get("subscription_name") not in [
                "messageAdded",
                "messageCancelled",
            ]:
                continue

            msg = (payload.get("data", {})).get("messageAdded", {})
            if not msg:
                continue

            if msg.get("author") == "human":
                continue

            chat_id: int = int(payload.get("unique_id")[13:])  # messageAdded:66642643

            await self.answer_queue[chat_id].put(msg)

    async def connect_to_channel(self):
        """连接到poe的websocket，用于拉取回答"""
        while True:
            # 获取ws地址
            await self.refresh_channel_data()
            async with ws_connect(self.channel_url) as ws:
                logger.info("已连接至ws channel")
                while True:
                    try:
                        data = await ws.recv()
                        await self.get_answer(loads(data))
                    except ws_ConnectionClosed:
                        logger.error("ws连接断开")
                        break
                    except Exception as e:
                        logger.error(f"ws连接出错：{repr(e)}")
                        break

    async def send_query(self, query_name: str, variables: dict) -> dict:
        """
        Send a query request.

        Args:
        - query_name (str): The name of the query.
        - variables (dict): The variables for the query.

        Returns:
        - dict: The response data.
        """
        data = generate_data(query_name, variables)
        base_string = data + self.formkey + "4LxgHM6KpFqokX0Ox"
        try:
            resp = await self.httpx_client.post(
                GQL_URL,
                content=data,
                headers={
                    "content-type": "application/json",
                    "poe-tag-id": md5(base_string.encode()).hexdigest(),
                },
            )
            json_data = loads(resp.text)

            if (
                "success" in json_data.keys()
                and not json_data["success"]
                or json_data["data"] is None
            ):
                err_msg: str = json_data["errors"][0]["message"]
                raise Exception(err_msg)

            return json_data
        except Exception as e:
            with open("error.json", "a") as a:
                dump(json_data, a, ensure_ascii=False)  # type:ignore
            raise Exception(f"执行请求【{query_name}】失败，错误信息：{e}")

    async def create_bot(self, model: str, prompt: str) -> tuple[str, int]:
        """
        Create a new bot using the specified configuration.

        Args:
        - model: The base model for the new bot.
        - prompt: The prompt for the new bot.

        Returns:
        - handle: The handle of the new bot.
        - bot_id: The ID of the new bot.
        """
        while True:
            handle = generate_random_handle()
            result = await self.send_query(
                "CreateBotMain_poeBotCreate_Mutation",
                {
                    "handle": handle,
                    "prompt": prompt,
                    "model": available_models[model][0],
                    "hasSuggestedReplies": False,
                    "displayName": None,
                    "isPromptPublic": True,
                    "introduction": "",
                    "description": "",
                    "profilePictureUrl": "",
                    "apiUrl": None,
                    "apiKey": None,
                    "isApiBot": False,
                    "hasLinkification": False,
                    "hasMarkdownRendering": True,
                    "isPrivateBot": False,
                    "temperature": None,
                },
            )
            json_data = result["data"]["poeBotCreate"]
            status = json_data["status"]
            if status != "success":
                if status == "handle_already_taken":
                    continue

                raise Exception(f"创建bot失败，错误信息：{status}")

            bot_id_b64 = json_data["bot"]["id"]
            bot_id = int(base64_decode(bot_id_b64)[4:])
            return handle, bot_id

    async def send_msg_to_new_chat(
        self, handle: str, question: str
    ) -> Tuple[int, int, str, int]:
        """
        发消息给一个新会话

        参数：
        - handle 要发送消息的机器人的唯一标识符。
        - question 要发送给机器人的消息。
        """
        message_data = await self.send_query(
            "chatHelpersSendNewChatMessageMutation",
            {
                "bot": handle,
                "query": question,
                "source": {
                    "chatInputMetadata": {"useVoiceRecord": False},
                    "sourceType": "chat_input",
                },
                "sdid": self.sdid,
                "attachments": [],
            },
        )
        data = message_data["data"]["messageEdgeCreate"]["chat"]
        message_id: int = data["messagesConnection"]["edges"][0]["node"]["messageId"]
        create_time: int = data["messagesConnection"]["edges"][0]["node"][
            "creationTime"
        ]
        chat_code: str = data["chatCode"]
        chat_id: int = data["chatId"]
        return message_id, create_time, chat_code, chat_id

    async def send_msg_to_old_chat(
        self, handle: str, chat_id: int, question: str
    ) -> tuple[int, int]:
        """
        发消息给一个旧会话

        参数：
        - handle 要发送消息的机器人的唯一标识符。
        - chat_id 要发送消息的机器人的唯一标识符。
        - question 要发送给机器人的消息。
        """
        message_data = await self.send_query(
            "chatHelpers_sendMessageMutation_Mutation",
            {
                "chatId": chat_id,
                "bot": handle.lower(),
                "query": question,
                "source": {
                    "sourceType": "chat_input",
                    "chatInputMetadata": {"useVoiceRecord": False},
                },
                "withChatBreak": False,
                "clientNonce": token_hex(8),
                "sdid": self.sdid,
                "attachments": [],
            },
        )
        message_id: int = message_data["data"]["messageEdgeCreate"]["message"]["node"][
            "messageId"
        ]
        create_time: int = message_data["data"]["messageEdgeCreate"]["message"]["node"][
            "creationTime"
        ]
        return message_id, create_time

    async def talk_to_bot(
        self, handle: str, chat_id: int, question: str
    ) -> AsyncGenerator:
        """
        向指定的机器人发送问题

        参数：
        - handle 要发送消息的机器人的唯一标识符。
        - chat_id 要发送消息的机器人的唯一标识符。
        - question 要发送给机器人的消息。
        """
        # channel地址刷新中
        if self.refresh_channel_lock:
            while True:
                await sleep(1)
                if self.refresh_channel_lock == False:
                    break

        # 半小时刷新一次channel地址
        if time() - self.refresh_channel_time >= 1800:
            if self.ws_client_task:
                self.refresh_channel_lock = True
                self.refresh_channel_time = time()
                # 等待当前回答生成完毕
                while self.talking:
                    await sleep(1)
                    if self.talking == False:
                        break
                self.ws_client_task.cancel()
                self.answer_queue.clear()
                self.cache_answer_msg_id.clear()
                self.ws_client_task = create_task(self.connect_to_channel())
                logger.info("已刷新ws channel地址")
                self.refresh_channel_lock = False

        self.talking = True

        try:
            if not chat_id:
                (
                    question_msg_id,
                    question_create_time,
                    chat_code,
                    chat_id,
                ) = await self.send_msg_to_new_chat(handle, question)
                yield NewChat(chat_code=chat_code, chat_id=chat_id)
            else:
                question_msg_id, question_create_time = await self.send_msg_to_old_chat(
                    handle, chat_id, question
                )
        except Exception as e:
            self.talking = False
            err_msg = f"获取bot【{handle}】的message id出错，错误信息：{e}"
            logger.error(err_msg)
            yield TalkError(content=err_msg)
            return

        # 创建答案生成队列
        if chat_id not in self.answer_queue:
            self.answer_queue[chat_id] = Queue()

        retry = 3
        last_text_len = 0
        get_answer_msg_id = False
        while retry >= 0:
            answer_data = await self.answer_queue[chat_id].get()

            if get_answer_msg_id == False:
                self.cache_answer_msg_id[handle] = answer_data.get("messageId")
                yield MsgId(
                    question_msg_id=question_msg_id,
                    question_create_time=question_create_time,
                    answer_msg_id=answer_data.get("messageId"),
                    answer_create_time=answer_data.get("creationTime"),
                )

            if answer_data.get("state") == "cancelled":
                yield End()
                return

            plain_text = answer_data.get("text")

            if answer_data.get("state") == "incomplete":
                new_text_len = len(plain_text)
                # 没有新的内容，略过
                if new_text_len == last_text_len:
                    continue

                retry = 3
                yield Text(content=plain_text[last_text_len:])
                last_text_len = new_text_len
                continue

            # 匹配到已完成
            if answer_data.get("state") == "complete":
                self.talking = False
                yield Text(content=plain_text[last_text_len:])
                yield End()
                return

            retry -= 1
            await sleep(1)

        self.talking = False
        err_msg = "获取回答超时"
        logger.error(err_msg)
        yield TalkError(content=err_msg)
        return

    async def talk_stop(self, handle: str):
        """
        停止生成回复

        参数：
        - handle 要发送消息的机器人的唯一标识符。
        """
        msg_id = self.cache_answer_msg_id[handle]
        try:
            await self.send_query(
                "chatHelpers_messageCancel_Mutation",
                {
                    "linkifiedTextLength": 1,
                    "messageId": msg_id,
                    "textLength": 1,
                },
            )
        except Exception as e:
            raise Exception(f"停止bot【{handle}】生成回答失败，错误信息：{e}")

    async def edit_bot(self, handle: str, bot_id: int, model: str, prompt: str):
        """
        这个函数用于编辑现有机器人的配置。

        参数：
        - handle 要编辑的机器人的URL名称。
        - bot_id 要发送消息的机器人的唯一标识符。
        - prompt 机器人的新提示。
        - model 机器人的新基础模型。
        """
        result = await self.send_query(
            "EditBotMain_poeBotEdit_Mutation",
            {
                "prompt": prompt,
                "baseBot": available_models[model][0],
                "botId": bot_id,
                "handle": handle,
                "displayName": handle,
                "isPromptPublic": True,
                "introduction": "",
                "description": "",
                "profilePictureUrl": "",
                "apiUrl": None,
                "apiKey": None,
                "hasLinkification": False,
                "hasMarkdownRendering": True,
                "hasSuggestedReplies": False,
                "isPrivateBot": False,
                "temperature": None,
            },
        )

        data = result["data"]["poeBotEdit"]
        if data["status"] != "success":
            raise Exception(f"编辑bot失败，错误信息：{data['status']}")

    async def send_chat_break(self, handle: str, chat_id: int):
        """
        重置对话，仅清除会话记忆，不会删除聊天记录。

        参数:
        - handle 要发送聊天终止信号的机器人的唯一标识符。
        - chat_id 与机器人的聊天的唯一标识符。
        """
        try:
            chat_id_b64 = base64_encode(f"Chat:{chat_id}")
            await self.send_query(
                "chatHelpers_addMessageBreakEdgeMutation_Mutation",
                {
                    "connections": [
                        f"client:{chat_id_b64}:__ChatMessagesView_chat_messagesConnection_connection"
                    ],
                    "chatId": chat_id,
                },
            )
        except Exception as e:
            raise Exception(f"bot【{handle}】重置对话失败，错误信息：{e}")

    async def delete_chat_by_chat_id(self, handle: str, chat_id: int):
        """
        删除某个bot下的会话

        参数:
        - handle 要发送聊天终止信号的机器人的唯一标识符。
        - chat_id 与机器人的聊天的唯一标识符。
        """
        try:
            await self.send_query(
                "useDeleteChat_deleteChat_Mutation", {"chatId": chat_id}
            )
        except Exception as e:
            raise Exception(f"删除bot【{handle}】失败，错误信息：{e}")

    async def delete_bot(self, handle: str, bot_id: int):
        """
        删除某个bot

        参数:
        - handle 要发送聊天终止信号的机器人的唯一标识符。
        - bot_id 与机器人的聊天的唯一标识符。
        """
        try:
            resp = await self.send_query(
                "BotInfoCardActionBar_poeBotDelete_Mutation", {"botId": bot_id}
            )
        except Exception as e:
            raise Exception(f"删除bot【{handle}】失败，错误信息：{e}")

        if resp["data"] is None and resp["errors"]:
            raise Exception(f"删除bot【{handle}】失败，错误信息：{resp['errors'][0]['message']}")

    async def get_chat_history(
        self, handle: str, chat_id: int, cursor: str
    ) -> tuple[list[dict], str]:
        """
        获取某个会话的历史记录

        参数:
        - handle 要发送聊天终止信号的机器人的唯一标识符。
        - chat_id 与机器人的聊天的唯一标识符。
        - cursor 坐标，用于翻页
        """
        try:
            result = await self.send_query(
                "ChatListPaginationQuery",
                {
                    "count": 25,
                    "cursor": cursor,
                    "id": base64_encode(f"Chat:{chat_id}"),
                },
            )
            _history = result["data"]["node"]["messagesConnection"]

            nodes: list[dict] = _history["edges"]
            has_pre_page: bool = _history["pageInfo"]["hasPreviousPage"]
            if has_pre_page:
                next_cursor: str = _history["pageInfo"]["startCursor"]
            else:
                next_cursor = "-1"

            result_list = []
            for node in nodes:
                n = node["node"]
                result_list.append(
                    {
                        "msg_id": n["messageId"],
                        "create_time": n["creationTime"],
                        "text": n["text"],
                        "author": "user" if n["author"] == "human" else "bot",
                    }
                )
        except Exception as e:
            raise Exception(f"拉取bot【{handle}】历史记录失败，错误信息：{e}")

        return result_list, next_cursor
