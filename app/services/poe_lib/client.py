from asyncio import (
    Event,
    Queue,
    TimeoutError,
    create_task,
    sleep,
    wait_for,
)
from hashlib import md5
from os import stat, stat_result
from random import randint
from re import sub
from secrets import token_hex
from traceback import format_exc
from typing import AsyncGenerator
from uuid import UUID, uuid5

from aiohttp import ClientSession, ClientTimeout, FormData, WSMsgType, request
from ujson import dump, dumps, load, loads
from utils.tool_util import debug_logger, logger

from .type import (
    BotMessageAdded,
    BotMessageCreated,
    ChatTitleUpdated,
    RefetchChannel,
    ServerError,
    TalkError,
)
from .util import (
    GQL_URL,
    GQL_URL_FILE,
    IMG_URL_CACHE,
    QUERY_HASH_PATH,
    SETTING_URL,
    SUB_HASH_PATH,
    base64_decode,
    base64_encode,
    filter_basic_bot_info,
    filter_bot_info,
    filter_bot_result,
    generate_data,
    generate_random_handle,
    str_time,
)


class Poe_Client:
    def __init__(self, p_b: str, p_lat: str, formkey: str, proxy: str | None = None):
        self.formkey = formkey
        self.p_b = p_b
        self.p_lat = p_lat
        self.sdid = ""
        self.proxy = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cookie": f"p-b={self.p_b}; p-lat={self.p_lat}",
            "Poe-Formkey": self.formkey,
            "Sec-Ch-Ua": '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://poe.com",
            "Referer": "https://poe.com/",
        }
        self.channel_url = ""
        self.hash_file_watch_task = None
        self.ws_client_task = None
        self.refresh_ws_event = Event()
        self.last_min_seq = 0
        self.ws_data_queue: dict[int, Queue] = {}
        self.get_chat_code: dict[str, int] = {}
        self.sub_hash: dict[str, str] = {}
        self.sub_hash_file_stat: stat_result
        self.query_hash: dict[str, str] = {}
        self.query_hash_file_stat: stat_result
        self.login_success: bool = False

    def refresh_ws_lock(self):
        self.refresh_ws_event.clear()

    def refresh_ws_unlock(self):
        self.refresh_ws_event.set()

    def refresh_ws_is_lock(self) -> bool:
        return not self.refresh_ws_event.is_set()

    async def login(self):
        """
        创建poe请求实例，可用于验证凭证是否有效，并拉取用户数据。
        """
        if not (self.p_b and self.formkey):
            raise Exception("p_b和formkey未正确填写，不登陆")

        self.login_success = False
        logger.info("Poe登陆中。。。。。。")
        self.read_sub_hash()
        self.read_query_hash()
        self.hash_file_watch_task = create_task(self.watch_hash_file())

        user_info = await self.get_account_info()
        text = f"\n登陆成功！账号信息如下\n -- 邮箱: {user_info['email']}\n -- 购买订阅: {user_info['subscriptionActivated']}"
        if user_info["subscriptionActivated"]:
            text += f"\n -- 订阅类型: {user_info['planType']}\n -- 订阅截止: {str_time(user_info['expireTime'])}\n -- 月度积分: {user_info['remainPoints']}/{user_info['monthPoints']}（{user_info['remainPoints']/user_info['monthPoints']*100:.2f}%）\n -- 重置时间: {str_time(user_info['pointsResetTime'])}"
        logger.info(text)
        self.login_success = True

        # 取消之前的ws连接
        if self.ws_client_task:
            self.ws_client_task.cancel()
        self.refresh_ws_unlock()
        return self

    def read_sub_hash(self):
        """
        读取sub_hash
        """
        self.sub_hash_file_stat = stat(SUB_HASH_PATH)
        with open(SUB_HASH_PATH, "r", encoding="utf-8") as r:
            self.sub_hash = load(r)

    def read_query_hash(self):
        """
        读取query_hash
        """
        self.query_hash_file_stat = stat(QUERY_HASH_PATH)
        with open(QUERY_HASH_PATH, "r", encoding="utf-8") as r:
            self.query_hash = load(r)

    async def watch_hash_file(self):
        """
        监听hash文件，热更新
        """
        while True:
            await sleep(1)
            _stat = stat(SUB_HASH_PATH)
            if _stat.st_mtime != self.sub_hash_file_stat.st_mtime:
                self.read_sub_hash()
                logger.warning("更新sub_hash")

            _stat = stat(QUERY_HASH_PATH)
            if _stat.st_mtime != self.query_hash_file_stat.st_mtime:
                self.read_query_hash()
                logger.warning("更新query_hash")

    async def send_query(
        self,
        query_name: str,
        variables: dict,
        forbidden_times: int = 0,
        file_list: list[tuple[str, bytes, str, str]] | None = None,
    ) -> dict:
        """
        发送请求
        """
        if self.login_success is False and query_name != "settingsPageQuery":
            raise Exception("未登录")

        if forbidden_times > 0:
            logger.warning(f"forbidden_times:{forbidden_times}")
            await sleep(randint(1, 2))

        status_code = 0
        try:
            if query_name == "get_edit_bot_info":
                async with request(
                    "GET",
                    f"https://poe.com/edit_bot?bot={variables['botName']}",
                    headers={"Cookie": f"p-b={self.p_b}; p-lat={self.p_lat}"},
                    timeout=ClientTimeout(5),
                    proxy=self.proxy,
                ) as response:
                    text = await response.text()

                pos = text.find('<script id="__NEXT_DATA__" type="application/json">')
                if pos != -1:
                    _json_str = text[pos + 51 :]
                    data = loads(_json_str[: _json_str.find("</script>")])
                    mainQuery = data["props"]["pageProps"]["data"]["mainQuery"]
                    return {
                        "basicBotList": mainQuery["viewer"][
                            "botsAllowedForUserCreation"
                        ],
                        "botInfo": mainQuery["bot"],
                    }

                raise Exception("获取自定义bot编辑信息失败")

            if query_name == "setting":
                async with request(
                    "GET",
                    SETTING_URL,
                    headers=self.headers,
                    timeout=ClientTimeout(5),
                    proxy=self.proxy,
                ) as response:
                    return loads(await response.text())

            # 发送带附件的问题
            if file_list:
                form = FormData()
                data = generate_data(query_name, variables, self.query_hash[query_name])
                base_string = data + self.formkey + "4LxgHM6KpFqokX0Ox"
                form.add_field("queryInfo", data, content_type="application/json")
                for file in file_list:
                    form.add_field(
                        file[0], file[1], content_type=file[2], filename=file[3]
                    )
                async with request(
                    "POST",
                    GQL_URL_FILE,
                    data=form,
                    headers={
                        **self.headers,
                        **{
                            "Poe-Queryname": query_name,
                            "poe-tag-id": md5(base_string.encode()).hexdigest(),
                        },
                    },
                    timeout=ClientTimeout(5),
                    proxy=self.proxy,
                ) as response:
                    status_code = response.status
                    text = await response.text()

            # 其他请求
            else:
                data = generate_data(query_name, variables, self.query_hash[query_name])
                base_string = data + self.formkey + "4LxgHM6KpFqokX0Ox"
                async with request(
                    "POST",
                    GQL_URL,
                    data=data,
                    headers={
                        **self.headers,
                        **{
                            "content-type": "application/json",
                            "Poe-Queryname": query_name,
                            "poe-tag-id": md5(base_string.encode()).hexdigest(),
                        },
                    },
                    timeout=ClientTimeout(5),
                    proxy=self.proxy,
                ) as response:
                    status_code = response.status
                    text = await response.text()

            try:
                json_data = loads(text)
            except:
                raise Exception(f"json解析出错: 源数据{text}")
            if json_data["data"] is None:
                if json_data["errors"][0]["message"] == "Server Error":
                    raise ServerError()

                raise Exception(text)

            return json_data

        except ServerError:
            raise ServerError("server error")

        except Exception as e:
            # if (
            #     # isinstance(e, ConnectError)
            #     # or isinstance(e, ConnectTimeout) or
            #     500 <= status_code < 600
            # ) and forbidden_times < 1:
            #     return await self.send_query(query_name, variables, forbidden_times + 1)

            err_code = f"status_code:{status_code}，" if status_code else ""
            raise Exception(
                f"执行请求【{query_name}】失败，{err_code}错误信息: {repr(e)}"
            )

    async def get_account_info(self) -> dict:
        """
        获取账号信息
        """
        try:
            result = await self.send_query("settingsPageQuery", {})
            _v = result["data"]["viewer"]
            self.sdid = str(
                uuid5(UUID("98765432101234567898765432101234"), _v["poeUser"]["id"])
            )

            data = {
                "email": _v["primaryEmail"],
                "subscriptionActivated": _v["subscription"]["isActive"],
                "planType": None,
                "expireTime": None,
                "remainPoints": _v["messagePointInfo"]["messagePointBalance"],
                "monthPoints": _v["messagePointInfo"]["totalMessagePointAllotment"],
                "pointsResetTime": _v["messagePointInfo"]["messagePointResetTime"]
                / 1000,
            }

            if data["subscriptionActivated"]:
                data["planType"] = _v["subscription"]["planType"]
                data["expireTime"] = _v["subscription"]["expiresTime"] / 1000

            return data

        except Exception as e:
            raise Exception(f"获取账号信息失败: {repr(e)}")

    async def explore_bot(self, category: str, cursor: str) -> dict:
        """
        探索bot列表

        参数:
        - category 类别名称
        - cursor 翻页指针，初始是0
        """
        try:
            if cursor == "0":
                result = await self.send_query(
                    "exploreBotsIndexPageQuery",
                    {"categoryName": category},
                )
                category_list: list[dict[str, str]] = [
                    {
                        "categoryName": _category["categoryName"],
                        "translatedCategoryName": _category["translatedCategoryName"],
                    }
                    for _category in result["data"]["exploreBotsCategoryObjects"]
                ]
            else:
                result = await self.send_query(
                    "ExploreBotsListPaginationQuery",
                    {
                        "categoryName": category,
                        "count": 25,
                        "cursor": cursor,
                    },
                )
                category_list = []

        except Exception as e:
            raise Exception(f"获取探索bot列表失败: {repr(e)}")

        bots = filter_bot_result(result["data"]["exploreBotsConnection"]["edges"])
        pageInfo: dict[str, str] = result["data"]["exploreBotsConnection"]["pageInfo"]

        return {
            "categoryList": category_list,
            "bots": bots,
            "pageInfo": pageInfo,
        }

    async def search_bot(self, key_word: str, cursor: str) -> dict:
        """
        搜索bot

        参数:
        - key_word 搜索关键字
        - cursor 翻页指针，初始是0
        """
        try:
            if cursor == "0":
                result = await self.send_query(
                    "SearchResultsMainQuery",
                    {"entityType": "bot", "searchQuery": key_word},
                )
            else:
                result = await self.send_query(
                    "SearchResultsListPaginationQuery",
                    {
                        "count": 10,
                        "cursor": cursor,
                        "entityType": "bot",
                        "query": key_word,
                    },
                )

        except Exception as e:
            raise Exception(f"获取搜索bot列表失败: {repr(e)}")

        bots = filter_bot_result(result["data"]["searchEntityConnection"]["edges"])
        pageInfo: dict[str, str] = result["data"]["searchEntityConnection"]["pageInfo"]

        return {
            "bots": bots,
            "pageInfo": pageInfo,
        }

    async def get_bot_info(self, botName: str) -> dict:
        """
        获取bot详细信息

        参数:
        - botName bot名称
        """
        try:
            result = await self.send_query(
                "HandleBotLandingPageQuery",
                {"botHandle": botName},
            )
            bot_info = filter_bot_info(result["data"]["bot"])
            return bot_info

        except Exception as e:
            raise Exception(f"获取bot详细信息失败: {repr(e)}")

    async def get_chat_info(self, chat_code: str, chat_id: int, cursor: str) -> dict:
        """
        获取chat详细信息

        参数:
        - chat_code
        - chat_id
        - cursor 坐标，用于翻页，初始为0
        """
        try:
            if cursor == "0":
                result = await self.send_query(
                    "ChatPageQuery",
                    {"chatCode": chat_code},
                )
            else:
                result = await self.send_query(
                    "ChatListPaginationQuery",
                    {
                        "count": 25,
                        "cursor": cursor,
                        "id": base64_encode(f"Chat:{chat_id}"),
                    },
                )

        except Exception as e:
            raise Exception(f"获取chat详细信息失败: {repr(e)}")

        if cursor == "0":
            botInfo = filter_bot_info(result["data"]["chatOfCode"]["defaultBotObject"])
            history_info = result["data"]["chatOfCode"]["messagesConnection"]
        else:
            botInfo = {}
            history_info = result["data"]["node"]["messagesConnection"]

        historyNodes = []
        edges = history_info["edges"]
        for edge in edges:
            historyNodes.append(
                {
                    "messageId": edge["node"]["messageId"],
                    "creationTime": edge["node"]["creationTime"],
                    "text": edge["node"]["text"],
                    "attachments": [
                        {
                            "name": a["name"],
                            "url": a["url"],
                        }
                        for a in edge["node"]["attachments"]
                    ],
                    "author": edge["node"]["author"]
                    if edge["node"]["author"] in ["chat_break", "human"]
                    else "bot",
                }
            )
        pageInfo = history_info["pageInfo"]

        return {
            "botInfo": botInfo,
            "historyNodes": historyNodes,
            "pageInfo": pageInfo,
        }

    async def get_new_channel(self):
        """
        此函数从设置_URL获取通道数据，更新ws地址，对话用的
        """
        result = await self.send_query("setting", {})
        tchannel_data = result["tchannelData"]
        self.headers["Poe-Tchannel"] = tchannel_data["channel"]
        ws_domain = f"tch{randint(1, int(1e6))}"[:8]
        self.channel_url = f'wss://{ws_domain}.tch.{tchannel_data["baseHost"]}/up/{tchannel_data["boxName"]}/updates?min_seq={tchannel_data["minSeq"]}&channel={tchannel_data["channel"]}&hash={tchannel_data["channelHash"]}'
        self.last_min_seq = int(tchannel_data["minSeq"])

        await self.send_query("subscriptionsMutation", self.sub_hash)

    async def refresh_channel(self, get_new_channel: bool = True):
        """
        刷新ws地址
        """
        # 如果已经锁了就返回
        if self.refresh_ws_is_lock():
            return
        # 取消之前的ws连接
        if self.ws_client_task:
            self.ws_client_task.cancel()
        # 锁定
        self.refresh_ws_lock()
        while self.refresh_ws_is_lock():
            try:
                if get_new_channel:
                    self.channel_url = ""
                    await self.get_new_channel()
                    # logger.info("更新ws地址成功")
                else:
                    self.channel_url = sub(
                        r"(min_seq=)\d+",
                        r"\g<1>" + str(self.last_min_seq),
                        self.channel_url,
                    )
                # 解除锁定
                self.refresh_ws_unlock()

            except Exception as e:
                logger.error(f"刷新ws地址失败，将重试，错误信息: {repr(e)}")

        # 创建新的ws连接任务
        self.ws_client_task = create_task(self.connect_to_channel())

    async def handle_ws_data(self, ws_data: dict):
        """
        处理ws中的数据
        """

        if "error" in ws_data:
            raise Exception(dumps(ws_data))

        messages: list[dict] = [
            loads(msg_str) for msg_str in ws_data.get("messages", "{}")
        ]
        for message in messages:
            message_type = message.get("message_type")
            if message_type == "refetchChannel":
                raise RefetchChannel()

            payload: dict = message["payload"]
            subscription_name = payload["subscription_name"]
            # 只要回答创建、生成、标题更新
            if subscription_name not in [
                "messageCreated",
                "messageAdded",
                "chatTitleUpdated",
            ]:
                if subscription_name not in [
                    "messagePointLimitUpdated",
                    "viewerStateUpdated",
                    "messageCancelled",
                    "messageDeleted",
                    "knowledgeSourceUpdated",
                ]:
                    logger.warning(
                        f"发现未知的subscription_name = {subscription_name}，数据已保存到本地"
                    )
                    with open(f"{subscription_name}.json", "w", encoding="utf-8") as w:
                        dump(message, w, indent=4, ensure_ascii=False)
                continue

            _data = payload["data"][subscription_name]
            debug_logger.info(_data)
            # 问题的消息数据
            if subscription_name == "messageCreated":
                data = BotMessageCreated(
                    messageId=_data["messageId"],
                    creationTime=_data["creationTime"],
                )
                # chat_code = _data["chat"]["chatCode"]
                chat_id = _data["chat"]["chatId"]
                # logger.warning(_data)
            # bot的回答数据
            elif subscription_name == "messageAdded":
                # 去掉空人类的问题、重置记忆
                if payload["data"]["messageAdded"]["author"] in ["human", "chat_break"]:
                    continue
                data = BotMessageAdded(
                    state=_data["state"],
                    text=_data["text"],
                )
                chat_id = int(payload["unique_id"][13:])
                # logger.warning(_data)
            # 会话标题更新 chatTitleUpdated
            else:
                data = ChatTitleUpdated(
                    title=_data["title"],
                )
                chat_id = int(payload["unique_id"][17:])
                # logger.warning(_data)

            # 创建接收回答的队列
            if chat_id not in self.ws_data_queue:
                self.ws_data_queue[chat_id] = Queue()

            await self.ws_data_queue[chat_id].put(data)

    async def connect_to_channel(self):
        """
        连接到poe的websocket，用于拉取回答
        """

        try:
            """创建ws连接"""
            async with ClientSession() as session:
                async with session.ws_connect(self.channel_url, proxy=self.proxy) as ws:
                    # logger.info("连接ws channel成功")
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            if msg.data != '{"type":"pong"}':
                                await self.handle_ws_data(loads(msg.data))
                        elif msg.type == WSMsgType.CLOSED:
                            break
                        elif msg.type == WSMsgType.ERROR:
                            break
                    await ws.close()

        except RefetchChannel:
            self.ws_data_queue.clear()
            logger.info("ws channel正常关闭")

        except Exception as e:
            logger.error(f"ws channel连接出错: {repr(e)}")
            logger.error(format_exc())

        self.ws_client_task = None

    async def send_question(
        self,
        handle: str,
        chat_id: int,
        question: str,
        price: int,
        files: list[tuple],
    ) -> dict:
        """
        向指定的机器人发送问题

        参数:
        - handle
        - chat_id
        - question  问题内容
        - price
        - files  附件
        """
        # channel地址刷新中
        await self.refresh_ws_event.wait()
        # 没有ws连接就创建
        if self.ws_client_task is None:
            await self.refresh_channel()

        try:
            result = await self.send_query(
                "sendMessageMutation",
                {
                    "attachments": [file[0] for file in files],
                    "bot": handle,
                    "chatId": chat_id if chat_id else None,
                    "clientNonce": token_hex(8),
                    "existingMessageAttachmentsIds": [],
                    "messagePointsDisplayPrice": price,
                    "query": question,
                    "sdid": self.sdid,
                    "shouldFetchChat": False if chat_id else True,
                    "source": {
                        "chatInputMetadata": {"useVoiceRecord": False},
                        "sourceType": "chat_input",
                    },
                },
                file_list=files,
            )

        except Exception as e:
            raise Exception(f"发送问题失败: {repr(e)}")

        result = result["data"]["messageEdgeCreate"]
        if result["status"] != "success":
            raise Exception(result["statusMessage"])

        botInfo = filter_bot_info(result["bot"])
        if chat_id == 0:
            chatCode = result["chat"]["chatCode"]
            chatId = result["chat"]["chatId"]
        else:
            chatCode = ""
            chatId = 0
        messageNode = {
            "messageId": result["message"]["node"]["messageId"],
            "creationTime": result["message"]["node"]["creationTime"],
            "text": result["message"]["node"]["text"],
            "attachments": [
                {
                    "name": a["name"],
                    "url": a["url"],
                }
                for a in result["message"]["node"]["attachments"]
            ],
            "author": "human",
        }

        return {
            "botInfo": botInfo,
            "chatCode": chatCode,
            "chatId": chatId,
            "messageNode": messageNode,
        }

    async def get_answer(
        self, chatId: int, questionMessageId: int, new_chat: bool
    ) -> AsyncGenerator:
        """
        拉取回答

        参数:
        - chatId
        - questionMessageId  问题的id
        - new_chat  是否为新会话
        """
        get_MessageCreated = False
        timeout = 15
        # 创建接收回答的队列
        while True:
            # 从队列拉取回复
            try:
                data = await wait_for(self.ws_data_queue[chatId].get(), timeout)
            except KeyError:
                self.ws_data_queue[chatId] = Queue()
                continue
            except TimeoutError:
                # 如果timeout不是15，说明就是差个title，可以不要
                if timeout != 15:
                    yield TalkError(errMsg="获取回答超时")
                return

            # 需要先拿到 BotMessageCreated
            if not get_MessageCreated:
                # 如果不是 BotMessageCreated 就忽略（因为这个一定是新消息的第一个）
                if not isinstance(data, BotMessageCreated):
                    continue
                # 如果是旧的也忽略
                if data.messageId < questionMessageId:
                    continue

            # 检查没问题就改True
            get_MessageCreated = True
            # 输出数据
            yield data

            if isinstance(data, BotMessageAdded):
                if data.state != "incomplete":
                    # 如果不是新会话直接返回
                    if not new_chat:
                        return
                    # 减少timeout，等title更新
                    timeout = 5

            # 如果新会话可能要更新title，在最后
            if isinstance(data, ChatTitleUpdated):
                return

    async def answer_again(self, chatCode: str, messageId: int, price: int):
        """
        重新生成回复

        参数:
        - chatCode
        - messageId  要重新回答的消息id
        - price  所需积分
        """
        try:
            await self.send_query(
                "regenerateMessageMutation",
                {"messageId": messageId, "messagePointsDisplayPrice": price},
            )
        except Exception as e:
            raise Exception(f"会话{chatCode}重新回答失败: {repr(e)}")

    async def talk_stop(self, chatCode: str, messageId: int, textLength: int = 0):
        """
        停止回答

        参数:
        - chatCode
        - messageId  要停止回答的消息id
        - textLength  不需要返回给前端就直接0
        """
        try:
            await self.send_query(
                "stopMessage_messageCancel_Mutation",
                {
                    "messageId": messageId,
                    "textLength": textLength,
                },
            )
        except Exception as e:
            raise Exception(f"会话{chatCode}停止回答失败: {repr(e)}")

    async def get_basic_bot_list(self) -> list[dict]:
        """
        获取自定义bot可使用的基础bot列表
        """
        try:
            result = await self.send_query(
                "createBotIndexPageQuery",
                {"messageId": None},
            )
        except Exception as e:
            raise Exception(f"获取基础bot列表失败: {repr(e)}")

        _bot_list: list = result["data"]["viewer"]["botsAllowedForUserCreation"]

        return filter_basic_bot_info(_bot_list)

    async def upload_knowledge_source(
        self, json_data: dict, files: list[tuple] | None = None
    ) -> dict:
        """
        上传bot引用资源

        参数:
        - json_data 上传的数据
            {"text_input": {"title": body.title, "content": body.content}}
            {"file_upload": {"attachment": "file"}}
        - files 二进制文件数据
        """
        try:
            result = await self.send_query(
                "knowledge_CreateKnowledgeSourceMutation",
                {"sourceInput": json_data},
                file_list=files,
            )

        except Exception as e:
            raise Exception(f"上传bot引用资源失败: {repr(e)}")

        if result["data"]["knowledgeSourceCreate"]["status"] != "success":
            err_msg = result["data"]["knowledgeSourceCreate"]["statusMessage"]
            raise Exception(f"上传bot引用资源失败: {err_msg}")

        _source = result["data"]["knowledgeSourceCreate"]["source"]
        sourceId: int = _source["knowledgeSourceId"]
        sourceTitle: int = _source["title"]

        data = {
            "sourceId": sourceId,
            "sourceTitle": sourceTitle,
        }
        return data

    async def get_text_knowledge_source(self, sourceId: int) -> dict:
        """
        获取bot引用资源内容（仅限文本）

        参数:
        - sourceId  资源id
        """
        try:
            result = await self.send_query(
                "KnowledgeSourceModalFlowQuery",
                {"knowledgeSourceId": sourceId, "shouldFetch": True},
            )

        except Exception as e:
            raise Exception(f"获取bot引用资源（仅限文本）失败: {repr(e)}")

        return {
            "title": result["data"]["knowledgeSource"]["title"],
            "content": result["data"]["knowledgeSource"]["content"],
        }

    async def edit_text_knowledge_source(self, sourceId: int, title: str, content: str):
        """
        编辑bot引用资源（仅限文本）

        参数:
        - sourceId  资源id
        - title  标题
        - content  内容
        """
        try:
            result = await self.send_query(
                "knowledge_EditKnowledgeSourceMutation",
                {
                    "knowledgeSourceId": sourceId,
                    "sourceInput": {"text_input": {"title": title, "content": content}},
                },
            )
        except Exception as e:
            raise Exception(f"编辑bot引用资源（仅限文本）失败: {repr(e)}")

        if result["data"]["knowledgeSourceEdit"]["status"] != "success":
            err_msg = result["data"]["knowledgeSourceEdit"]["statusMessage"]
            raise Exception(f"获取bot引用资源（仅限文本）失败: {err_msg}")

    async def create_bot(
        self,
        baseBotId: int,
        baseBotModel: str,
        description: str,
        prompt: str,
        citeSource: bool,
        sourceIds: list[int] = [],
    ) -> dict:
        """
        创建bot

        参数:
        - baseBotId  基础bot id
        - baseBotModel  基础bot模型
        - description  描述
        - prompt  预设
        - citeSource  是否引用资源
        - sourceIds  要引用的资源id
        """
        while True:
            handle = generate_random_handle(20)
            try:
                result = await self.send_query(
                    "CreateBotMain_poeBotCreate_Mutation",
                    {
                        "allowRelatedBotRecommendations": False,
                        "apiKey": generate_random_handle(32),
                        "apiUrl": None,
                        "baseBotId": baseBotId,
                        "customMessageLimit": None,
                        "description": description,
                        "displayName": None,
                        "handle": handle,
                        "hasMarkdownRendering": True,
                        "hasSuggestedReplies": False,
                        "introduction": "",
                        "isApiBot": False,
                        "isPrivateBot": True,
                        "isPromptPublic": False,
                        "knowledgeSourceIds": sourceIds,
                        "messagePriceCc": None,
                        "model": baseBotModel,
                        "profilePictureUrl": None,
                        "prompt": prompt,
                        "shouldCiteSources": citeSource,
                        "temperature": None,
                    },
                )
            except Exception as e:
                raise Exception(f"创建bot失败: {repr(e)}")

            poeBotCreate = result["data"]["poeBotCreate"]
            status = poeBotCreate["status"]
            if status != "success":
                if status == "handle_already_taken":
                    await sleep(1)
                    continue
                raise Exception(f"创建bot失败: {status} {str(result)}")
            break

        bot_id = int(base64_decode(poeBotCreate["bot"]["id"])[4:])
        return {
            "imgUrl": IMG_URL_CACHE["null"],
            "botType": "自定义",
            "botHandle": poeBotCreate["bot"]["handle"],
            "botId": bot_id,
        }

    async def get_edit_bot_info(self, botName: str) -> dict:
        """
        获取待编辑bot信息

        参数:
        - botName  bot名称
        """
        try:
            _bot_info = await self.send_query("get_edit_bot_info", {"botName": botName})
        except Exception as e:
            raise Exception(f"获取待编辑bot信息失败: {repr(e)}")

        sourceList = [
            {
                "sourceId": s["node"]["knowledgeSourceId"],
                "sourceType": (
                    "file"
                    if s["node"]["__typename"] == "FileUploadKnowledgeSource"
                    else "text"
                ),
                "title": s["node"]["title"],
                "lastUpdatedTime": s["node"]["lastUpdatedTime"],
            }
            for s in _bot_info["botInfo"]["knowledgeSourceConnection"]["edges"]
        ]

        bot_info = {
            "basicBotList": filter_basic_bot_info(_bot_info["basicBotList"]),
            "botInfo": {
                "botName": botName,
                "botId": _bot_info["botInfo"]["botId"],
                "botHandle": _bot_info["botInfo"]["handle"],
                "baseBotId": _bot_info["botInfo"]["baseBotId"],
                "baseBotModel": _bot_info["botInfo"]["model"],
                "description": _bot_info["botInfo"]["description"],
                "prompt": _bot_info["botInfo"]["promptPlaintext"],
                "citeSource": _bot_info["botInfo"]["shouldCiteSources"],
                "sourceList": sourceList,
            },
        }

        return bot_info

    async def edit_bot(
        self,
        botId: int,
        botHandle: str,
        baseBotId: int,
        baseBotModel: str,
        description: str,
        prompt: str,
        citeSource: bool,
        addSourceIds: list[int] = [],
        removeSourceIds: list[int] = [],
    ):
        """
        编辑bot设置

        参数:
        - botId  唯一值，不用动
        - botHandle  唯一值，不用动
        - baseBotId  基础bot id
        - baseBotModel  基础bot模型
        - description  描述
        - prompt  预设
        - citeSource  是否引用资源
        - addSourceIds  要增加的资源id
        - removeSourceIds  要删除的资源id
        """
        try:
            result = await self.send_query(
                "EditBotMain_poeBotEdit_Mutation",
                {
                    "allowRelatedBotRecommendations": False,
                    "apiKey": None,
                    "apiUrl": None,
                    "baseBot": baseBotModel,
                    "baseBotId": baseBotId,
                    "botId": botId,
                    "customMessageLimit": None,
                    "description": description,
                    "displayName": None,
                    "handle": botHandle,
                    "hasLinkification": False,
                    "hasMarkdownRendering": True,
                    "hasSuggestedReplies": False,
                    "introduction": "",
                    "isPrivateBot": True,
                    "isPromptPublic": False,
                    "knowledgeSourceIdsToAdd": addSourceIds,
                    "knowledgeSourceIdsToRemove": removeSourceIds,
                    "messagePriceCc": None,
                    "profilePictureUrl": "",
                    "prompt": prompt,
                    "shouldCiteSources": citeSource,
                    "temperature": None,
                },
            )
        except Exception as e:
            raise Exception(f"编辑bot失败: {repr(e)}")

        data = result["data"]["poeBotEdit"]
        if data["status"] != "success":
            raise Exception(f"编辑bot失败: {data['status']}")

    async def send_chat_break(self, chatCode: str, chat_id: int) -> dict:
        """
        重置对话，仅清除会话记忆，不会删除聊天记录。

        参数:
        - chatCode 会话code
        - chat_id 会话id
        """
        try:
            result = await self.send_query(
                "sendChatBreakMutation",
                {
                    "chatId": chat_id,
                    "clientNonce": token_hex(8),
                },
            )
        except Exception as e:
            raise Exception(f"会话{chatCode}清除上下文失败: {repr(e)}")

        _data = result["data"]["messageBreakEdgeCreate"]["message"]["node"]
        data = {
            "messageId": _data["messageId"],
            "creationTime": _data["creationTime"],
            "text": "",
            "attachments": [],
            "author": "chat_break",
        }
        return data

    async def delete_chat(self, chat_code: str, chat_id: int):
        """
        删除会话

        参数:
        - chat_code 会话code
        - chat_id 会话id
        """
        try:
            await self.send_query(
                "useDeleteChat_deleteChat_Mutation", {"chatId": chat_id}
            )
        except Exception as e:
            raise Exception(f"会话{chat_code}删除失败: {repr(e)}")

    async def delete_bot(self, botName: str, bot_id: int):
        """
        删除bot

        参数:
        - botName bot名称
        - bot_id bot id
        """
        try:
            resp = await self.send_query(
                "BotInfoCardActionBar_poeBotDelete_Mutation", {"botId": bot_id}
            )
        except Exception as e:
            raise Exception(f"bot {botName} 删除失败: {repr(e)}")

        if resp["data"] is None and resp["errors"]:
            raise Exception(f"bot {botName} 删除失败: {resp['errors'][0]['message']}")
