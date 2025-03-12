from asyncio import (
    Lock,
    Queue,
    TimeoutError,
    create_task,
    sleep,
    wait_for,
)
from hashlib import md5
from os import path
from random import randint
from re import findall
from secrets import token_hex
from traceback import format_exc
from typing import AsyncGenerator
from uuid import UUID, uuid5

from aiohttp import (
    ClientSession,
    ClientTimeout,
    FormData,
    WSMsgType,
    request,
)
from ujson import dump, load, loads
from utils.tool_util import debug_logger, logger

from .type import (
    BotMessageAdd,
    ChatTitleUpdated,
    FileTooLarge,
    NeedDeleteChat,
    PriceCache,
    PriceCost,
    RefetchChannel,
    ServerError,
    TalkError,
    UnsupportedFileType,
)
from .util import (
    GQL_URL,
    GQL_URL_FILE,
    HASHES_PATH,
    IMG_URL_CACHE,
    SETTING_URL,
    base64_decode,
    base64_encode,
    filter_basic_bot_info,
    filter_bot_result,
    filter_files_info,
    generate_data,
    generate_random_handle,
    get_img_url,
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cookie": f"p-b={self.p_b}; p-lat={self.p_lat}",
            "Origin": "https://poe.com",
            "Poe-Formkey": self.formkey,
            "priority": "u=1, i",
            "Referer": "https://poe.com/",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
        }
        self.channel_url = ""
        self.ws_client_task = None
        self.last_min_seq = 0
        self.ws_data_queue: dict[int, Queue] = {}
        self.get_chat_code: dict[str, int] = {}
        self.hashes: dict[str, str] = {}
        self.login_success: bool = False
        self.send_question_lock: Lock = Lock()
        self.bot_price_cache: dict[str, PriceCache] = {}

    async def login(self):
        """
        创建poe请求实例，可用于验证凭证是否有效，并拉取用户数据。
        """
        if not (self.p_b and self.formkey):
            raise Exception("p_b和formkey未正确填写，不登陆")

        self.login_success = False
        logger.info("Poe登陆中。。。。。。")
        await self.read_hashes()

        user_info = await self.get_account_info()
        text = f"\n登陆成功！账号信息如下\n -- 邮箱: {user_info['email']}\n -- 购买订阅: {user_info['subscriptionActivated']}"
        if user_info["subscriptionActivated"]:
            text += f"\n -- 订阅类型: {user_info['planType']}\n -- 订阅截止: {str_time(user_info['expireTime'])}\n -- 月度积分: {user_info['remainPoints']}/{user_info['monthPoints']}（{user_info['remainPoints'] / user_info['monthPoints'] * 100:.2f}%）\n -- 重置时间: {str_time(user_info['pointsResetTime'])}"
        logger.info(text)
        self.login_success = True

        # 取消之前的ws任务
        if self.ws_client_task:
            self.ws_client_task.cancel()
        # 创建ws任务
        self.ws_client_task = create_task(self.connect_to_channel())

        return self

    async def read_hashes(self):
        """
        读取hashes
        """
        if path.exists(HASHES_PATH):
            with open(HASHES_PATH, "r", encoding="utf-8") as r:
                self.hashes = load(r)
        else:
            logger.warning("未发现hashes.json文件，正在拉取，大概需要1~2分钟")
            await self.update_hashes()

    async def update_hashes(self):
        async with request(
            "GET",
            "https://poe.com/login?redirect_url=%2F",
            headers=self.headers,
            timeout=ClientTimeout(5),
            proxy=self.proxy,
        ) as response:
            text = await response.text()

        chunks_regex = (
            r"https:\/\/psc2\.cf2\.poecdn\.net\/assets\/_next\/static\/chunks.+?\.js"
        )
        manifest_regex = r"https:\/\/psc2\.cf2\.poecdn\.net\/assets\/_next\/static\/\S{21}\/_buildManifest\.js"
        webpack_regex = r"https:\/\/psc2\.cf2\.poecdn\.net\/assets\/_next\/static\/chunks\/webpack.+?.js"
        base_regex = r"https:\/\/psc2\.cf2\.poecdn\.net\/assets\/_next\/"

        chunks = findall(chunks_regex, text)
        manifest_url = findall(manifest_regex, text)[0]
        webpack_url = findall(webpack_regex, text)[0]
        base_url = findall(base_regex, text)[0]

        async with request(
            "GET",
            manifest_url,
            headers=self.headers,
            timeout=ClientTimeout(5),
            proxy=self.proxy,
        ) as response:
            text = await response.text()

        resources_regex = r'"(static/.+?)"'
        resources_list = findall(resources_regex, text)
        urls = []

        async with request(
            "GET",
            webpack_url,
            headers=self.headers,
            timeout=ClientTimeout(5),
            proxy=self.proxy,
        ) as response:
            text = await response.text()

        webpack_chunks_regex = r'\+\(({.+?})\)\[.\]\+"\.js"'
        webpack_items_regex = r'(\d+):"([0-9a-zA-Z]{16})"'
        json_text = findall(webpack_chunks_regex, text)[0]
        webpack_chunks = findall(webpack_items_regex, json_text)

        for chunk_id, chunk_hash in webpack_chunks:
            urls.append(base_url + f"static/chunks/{chunk_id}.{chunk_hash}.js")
        for resource in resources_list:
            urls.append(base_url + resource)
        urls = list(set(urls + chunks))

        queries = {}
        for url in urls:
            if not url.endswith(".js"):
                continue

            async with request(
                "GET",
                url,
                headers=self.headers,
                timeout=ClientTimeout(5),
                proxy=self.proxy,
            ) as response:
                if response.status != 200:
                    continue

                text = await response.text()

            hashes_regex = r'params:{id:"([0-9a-zA-Z]{64})".+?name:"(\S+?)"'
            hashes_list = findall(hashes_regex, text)

            for query_hash, query_name in hashes_list:
                if "_" in query_name:
                    query_name = query_name.split("_")[1]
                query_name = query_name[0].upper() + query_name[1:]
                queries[query_name] = query_hash

        with open(HASHES_PATH, "w", encoding="utf-8") as w:
            dump(queries, w, indent=4, sort_keys=True)
        self.hashes = queries
        logger.info("更新hashes文件完毕")

    async def send_query(
        self,
        query_name: str,
        variables: dict,
        hash: str,
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
            await sleep(randint(2, 3))

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
                        "basicBotViewer": mainQuery["viewer"],
                        "botInfo": mainQuery["bot"],
                    }
                    # return {
                    #     "basicBotList": mainQuery["viewer"][
                    #         "botsAllowedForUserCreation"
                    #     ],
                    #     "botInfo": mainQuery["bot"],
                    # }

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
                data = generate_data(query_name, variables, hash)
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
                    # logger.warning(f"get {query_name}  {status_code}")
                    text = await response.text()

            # 其他请求
            else:
                data = generate_data(query_name, variables, hash)
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
                    # logger.warning(f"post {query_name}  {status_code}")
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
            if (400 <= status_code < 600) and forbidden_times < 3:
                return await self.send_query(
                    query_name, variables, hash, forbidden_times + 1, file_list
                )

            err_code = f"status_code:{status_code}，" if status_code else ""
            raise Exception(
                f"执行请求【{query_name}】失败，{err_code}错误信息: {repr(e)}"
            )

    async def get_account_info(self) -> dict:
        """
        获取账号信息
        """
        try:
            result = await self.send_query(
                "settingsPageQuery", {}, self.hashes["SettingsPageQuery"]
            )
            _v = result["data"]["viewer"]
            self.sdid = str(
                uuid5(UUID("98765432101234567898765432101234"), _v["poeUser"]["id"])
            )

            data = {
                "email": _v["primaryEmail"],
                "subscriptionActivated": True
                if _v["subscription"]["subscriptionProduct"]
                else False,
                "planType": None,
                "expireTime": None,
                "remainPoints": _v["messagePointInfo"]["messagePointBalance"],
                "monthPoints": _v["messagePointInfo"]["totalMessagePointAllotment"],
                "pointsResetTime": _v["messagePointInfo"]["messagePointResetTime"]
                / 1000,
            }

            if data["subscriptionActivated"]:
                data["planType"] = (
                    f"{_v['subscription']['subscriptionProduct']['displayName']} ({_v['subscription']['subscriptionProduct']['paidSubscriptionPeriod']})"
                )
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
                    self.hashes["ExploreBotsIndexPageQuery"],
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
                    self.hashes["ExploreBotsListPaginationQuery"],
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
                    self.hashes["SearchResultsMainQuery"],
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
                    self.hashes["SearchResultsListPaginationQuery"],
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
                self.hashes["HandleBotLandingPageQuery"],
            )
            if result["data"]["bot"]:
                return await self.filter_bot_info(result["data"]["bot"])

        except Exception as e:
            raise Exception(f"获取bot详细信息失败: {repr(e)}")

        raise Exception("bot不存在（可能被删除了）")

    async def get_lastest_historyNode(self, chat_id: int, messageId: int) -> dict:
        """
        获取最后一个消息记录，用户拉取回答超时的时候用
        """
        try:
            result = await self.send_query(
                "ChatListPaginationQuery",
                {
                    "count": 25,
                    "cursor": "0",
                    "id": base64_encode(f"Chat:{chat_id}"),
                },
                self.hashes["ChatListPaginationQuery"],
            )
        except Exception as e:
            raise Exception(f"获取chat详细信息失败: {repr(e)}")

        edge = result["data"]["node"]["messagesConnection"]["edges"][-1]
        historyNode = {
            "messageId": edge["node"]["messageId"],
            "creationTime": edge["node"]["creationTime"],
            "text": edge["node"]["text"],
            "attachments": filter_files_info(edge["node"]["attachments"]),
        }

        if historyNode["messageId"] < messageId:
            return {}

        return historyNode

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
                    self.hashes["ChatPageQuery"],
                )
            else:
                result = await self.send_query(
                    "ChatListPaginationQuery",
                    {
                        "count": 25,
                        "cursor": cursor,
                        "id": base64_encode(f"Chat:{chat_id}"),
                    },
                    self.hashes["ChatListPaginationQuery"],
                )

        except Exception as e:
            raise Exception(f"获取chat详细信息失败: {repr(e)}")

        if cursor == "0":
            botInfo = await self.filter_bot_info(
                result["data"]["chatOfCode"]["defaultBotObject"]
            )
            history_info = result["data"]["chatOfCode"]["messagesConnection"]
        else:
            botInfo = {}
            history_info = result["data"]["node"]["messagesConnection"]

        historyNodes = []
        for edge in history_info["edges"]:
            historyNodes.append(
                {
                    "messageId": edge["node"]["messageId"],
                    "creationTime": edge["node"]["creationTime"],
                    "text": edge["node"]["text"],
                    "attachments": filter_files_info(edge["node"]["attachments"]),
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
        result = await self.send_query("setting", {}, "")

        tchannel_data = result["tchannelData"]
        self.headers["Poe-Tchannel"] = tchannel_data["channel"]
        ws_domain = f"tch{randint(1, int(1e6))}"[:8]
        self.channel_url = f"wss://{ws_domain}.tch.{tchannel_data['baseHost']}/up/{tchannel_data['boxName']}/updates?min_seq={tchannel_data['minSeq']}&channel={tchannel_data['channel']}&hash={tchannel_data['channelHash']}"
        self.last_min_seq = int(tchannel_data["minSeq"])

        await self.send_query(
            "subscriptionsMutation",
            {
                "subscriptions": [
                    {
                        "subscriptionName": "messageAdded",
                        "query": None,
                        "queryHash": self.hashes["MessageAdded"],
                    },
                    {
                        "subscriptionName": "messageCancelled",
                        "query": None,
                        "queryHash": self.hashes["MessageCancelled"],
                    },
                    {
                        "subscriptionName": "messageDeleted",
                        "query": None,
                        "queryHash": self.hashes["MessageDeleted"],
                    },
                    {
                        "subscriptionName": "messageRead",
                        "query": None,
                        "queryHash": self.hashes["MessageRead"],
                    },
                    {
                        "subscriptionName": "messageCreated",
                        "query": None,
                        "queryHash": self.hashes["MessageCreated"],
                    },
                    {
                        "subscriptionName": "messageStateUpdated",
                        "query": None,
                        "queryHash": self.hashes["MessageStateUpdated"],
                    },
                    {
                        "subscriptionName": "messageAttachmentAdded",
                        "query": None,
                        "queryHash": self.hashes["MessageAttachmentAdded"],
                    },
                    {
                        "subscriptionName": "messageFollowupActionAdded",
                        "query": None,
                        "queryHash": self.hashes["MessageFollowupActionAdded"],
                    },
                    {
                        "subscriptionName": "messageMetadataUpdated",
                        "query": None,
                        "queryHash": self.hashes["MessageMetadataUpdated"],
                    },
                    {
                        "subscriptionName": "messageReactionsUpdated",
                        "query": None,
                        "queryHash": self.hashes["MessageReactionsUpdated"],
                    },
                    {
                        "subscriptionName": "messageTextUpdated",
                        "query": None,
                        "queryHash": self.hashes["MessageTextUpdated"],
                    },
                    {
                        "subscriptionName": "jobStarted",
                        "query": None,
                        "queryHash": self.hashes["JobStarted"],
                    },
                    {
                        "subscriptionName": "jobUpdated",
                        "query": None,
                        "queryHash": self.hashes["JobUpdated"],
                    },
                    {
                        "subscriptionName": "jobCostUpdated",
                        "query": None,
                        "queryHash": self.hashes["JobCostUpdated"],
                    },
                    {
                        "subscriptionName": "viewerStateUpdated",
                        "query": None,
                        "queryHash": self.hashes["ViewerStateUpdated"],
                    },
                    {
                        "subscriptionName": "unreadChatsUpdated",
                        "query": None,
                        "queryHash": self.hashes["UnreadChatsUpdated"],
                    },
                    {
                        "subscriptionName": "canvasTabClosed",
                        "query": None,
                        "queryHash": self.hashes["CanvasTabClosed"],
                    },
                    {
                        "subscriptionName": "canvasTabOpened",
                        "query": None,
                        "queryHash": self.hashes["CanvasTabOpened"],
                    },
                    {
                        "subscriptionName": "canvasTabBackgrounded",
                        "query": None,
                        "queryHash": self.hashes["CanvasTabBackgrounded"],
                    },
                    {
                        "subscriptionName": "chatTitleUpdated",
                        "query": None,
                        "queryHash": self.hashes["ChatTitleUpdated"],
                    },
                    {
                        "subscriptionName": "chatDeleted",
                        "query": None,
                        "queryHash": self.hashes["ChatDeleted"],
                    },
                    {
                        "subscriptionName": "knowledgeSourceUpdated",
                        "query": None,
                        "queryHash": self.hashes["KnowledgeSourceUpdated"],
                    },
                    {
                        "subscriptionName": "messagePointLimitUpdated",
                        "query": None,
                        "queryHash": self.hashes["MessagePointLimitUpdated"],
                    },
                    {
                        "subscriptionName": "chatMemberAddedWithContext",
                        "query": None,
                        "queryHash": self.hashes["ChatMemberAddedWithContext"],
                    },
                    {
                        "subscriptionName": "chatSettingsUpdated",
                        "query": None,
                        "queryHash": self.hashes["ChatSettingsUpdated"],
                    },
                    {
                        "subscriptionName": "chatModalStateChanged",
                        "query": None,
                        "queryHash": self.hashes["ChatModalStateChanged"],
                    },
                    {
                        "subscriptionName": "defaultBotOfChatChanged",
                        "query": None,
                        "queryHash": self.hashes["DefaultBotOfChatChanged"],
                    },
                    {
                        "subscriptionName": "messageFollowupActionUpdated",
                        "query": None,
                        "queryHash": self.hashes["MessageFollowupActionUpdated"],
                    },
                ]
            },
            self.hashes["SubscriptionsMutation"],
        )

    async def handle_ws_data(self, ws_data: dict):
        """
        处理ws中的数据
        """

        if "error" in ws_data:
            logger.warning(f"get {ws_data}")
            raise RefetchChannel("error")

        messages: list[dict] = [
            loads(msg_str) for msg_str in ws_data.get("messages", "{}")
        ]
        for message in messages:
            message_type = message.get("message_type")
            if message_type == "refetchChannel":
                raise RefetchChannel("refetch")

            payload: dict = message["payload"]
            subscription_name = payload["subscription_name"]
            # 只要回答创建、生成、标题更新
            if subscription_name not in [
                "messageAdded",
                "chatTitleUpdated",
                "jobCostUpdated",
            ]:
                if subscription_name not in [
                    "messageRead",
                    "messageCreated",
                    "messagePointLimitUpdated",
                    "viewerStateUpdated",
                    "messageCancelled",
                    "messageDeleted",
                    "knowledgeSourceUpdated",
                    "jobUpdated",
                    "messageFollowupActionUpdated",
                    "jobStarted",
                    "chatDeleted",
                ]:
                    logger.warning(
                        f"发现未知的subscription_name = {subscription_name}，数据已保存到本地"
                    )
                    with open(f"{subscription_name}.json", "w", encoding="utf-8") as w:
                        dump(message, w, indent=4, ensure_ascii=False)
                continue

            _data = payload["data"][subscription_name]
            # bot的回答数据
            if subscription_name == "messageAdded":
                # 去掉空人类的问题、重置记忆
                if payload["data"]["messageAdded"]["author"] in ["human", "chat_break"]:
                    continue
                data = BotMessageAdd(
                    state=_data["state"],
                    messageStateText=_data["messageStateText"]
                    if "messageStateText" in _data
                    else None,
                    messageId=_data["messageId"],
                    creationTime=_data["creationTime"],
                    text=_data["text"],
                    attachments=filter_files_info(_data["attachments"]),
                )
                chat_id = int(payload["unique_id"][13:])

            # 会话标题更新
            elif subscription_name == "chatTitleUpdated":
                data = ChatTitleUpdated(
                    title=_data["title"],
                )
                chat_id = int(payload["unique_id"][17:])
            # 花费更新
            else:
                data = PriceCost(price=_data["totalCostPoints"])
                chat_id = int(_data["trigger"]["message"]["chat"]["chatId"])

            # 创建接收回答的队列
            if chat_id not in self.ws_data_queue:
                self.ws_data_queue[chat_id] = Queue()

            await self.ws_data_queue[chat_id].put(data)

    async def connect_to_channel(self):
        """
        连接到poe的websocket，用于拉取回答
        """
        error_times = 0
        while error_times < 3:
            try:
                """获取ws地址"""
                await self.get_new_channel()
                """创建ws连接"""
                async with ClientSession(
                    headers={
                        "Accept-Encoding": "gzip",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                        "Cache-Control": "no-cache",
                        "Connection": "Upgrade",
                        "Origin": "https://poe.com",
                        "Pragma": "no-cache",
                        "Upgrade": "websocket",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
                    }
                ) as session:
                    logger.info("ws channel connected")
                    async with session.ws_connect(
                        self.channel_url, proxy=self.proxy, autoping=True, heartbeat=30
                    ) as ws:
                        try:
                            async for msg in ws:
                                debug_logger.debug(msg.data)
                                if msg.type == WSMsgType.TEXT:
                                    await self.handle_ws_data(loads(msg.data))
                                else:
                                    logger.warning(f"get unknown ws type: {msg.type}")
                                    break
                        finally:
                            await ws.close()

                error_times = 0

            except RefetchChannel as e:
                logger.warning({repr(e)})
                error_times = 0

            except Exception as e:
                logger.error(f"ws channel连接出错: {repr(e)}")
                logger.error(format_exc())
                error_times += 1

        logger.warning("ws channel disconnected")
        self.ws_client_task = None

    async def send_question(
        self,
        handle: str,
        chat_id: int,
        question: str,
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
        if self.ws_client_task is None:
            # 创建ws任务
            self.ws_client_task = create_task(self.connect_to_channel())
            await sleep(1)

        try:
            result = await self.send_query(
                "sendMessageMutation",
                {
                    "attachments": [file[0] for file in files],
                    "bot": handle,
                    "chatId": chat_id if chat_id else None,
                    "clientNonce": token_hex(8),
                    "existingMessageAttachmentsIds": [],
                    "messagePointsDisplayPrice": self.bot_price_cache[
                        handle
                    ].displayPrice,
                    "query": question,
                    "referencedMessageId": None,
                    "sdid": self.sdid,
                    "shouldFetchChat": False if chat_id else True,
                    "source": {
                        "chatInputMetadata": {"useVoiceRecord": False},
                        "sourceType": "chat_input",
                    },
                },
                self.hashes["SendMessageMutation"],
                file_list=files,
            )

        except Exception as e:
            raise Exception(f"发送问题失败: {repr(e)}")

        # logger.error(dumps(result, ensure_ascii=False))
        result = result["data"]["messageEdgeCreate"]
        if result["status"] != "success":
            if result["status"] == "unsupported_file_type":
                raise UnsupportedFileType()

            if result["status"] == "file_too_large":
                raise FileTooLarge()

            if result["status"] == "no_access":
                raise NeedDeleteChat()

            raise Exception(result["statusMessage"])

        botInfo = await self.filter_bot_info(result["bot"])
        if chat_id == 0:
            chatCode = result["chat"]["chatCode"]
            chatId = result["chat"]["chatId"]
        else:
            chatCode = ""
            chatId = 0
        messageNode = {
            "state": result["message"]["node"]["state"],
            "messageId": result["message"]["node"]["messageId"],
            "creationTime": result["message"]["node"]["creationTime"],
            "text": result["message"]["node"]["text"],
            "attachments": filter_files_info(result["message"]["node"]["attachments"]),
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
                if _data := await self.get_lastest_historyNode(
                    chatId, questionMessageId
                ):
                    logger.warning("获取回答超时，但拉了回来")
                    data = BotMessageAdd(
                        state="complete",
                        messageStateText=_data["messageStateText"]
                        if "messageStateText" in _data
                        else None,
                        messageId=_data["messageId"],
                        creationTime=_data["creationTime"],
                        text=_data["text"],
                        attachments=filter_files_info(_data["attachments"]),
                    )
                    yield data
                    return

                yield TalkError(errMsg="获取回答超时")
                return

            if isinstance(data, BotMessageAdd):
                # 如果是旧的也忽略
                if data.messageId < questionMessageId:
                    continue
                yield data

            # 消费更新
            if isinstance(data, PriceCost):
                yield data
                # 如果不是新会话，直接返回
                if not new_chat:
                    return

            # 如果新会话要更新title，在最后
            if isinstance(data, ChatTitleUpdated):
                yield data
                return

    async def answer_again(self, handle: str, chatCode: str, messageId: int):
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
                {
                    "messageId": messageId,
                    "messagePointsDisplayPrice": self.bot_price_cache[
                        handle
                    ].displayPrice,
                },
                self.hashes["RegenerateMessageMutation"],
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
                self.hashes["MessageCancel"],
            )
        except Exception as e:
            raise Exception(f"会话{chatCode}停止回答失败: {repr(e)}")

    async def get_basic_bot_data(self) -> dict:
        """
        获取自定义bot可使用的基础bot列表
        """
        try:
            result = await self.send_query(
                "createBotIndexPageQuery",
                {
                    "canvasNodeId": "",
                    "includeCanvasData": False,
                    "messageId": None,
                },
                self.hashes["CreateBotIndexPageQuery"],
            )
        except Exception as e:
            raise Exception(f"获取基础bot列表失败: {repr(e)}")

        _data = result["data"]["viewer"]

        basic_bot_list = filter_basic_bot_info(_data["botsAllowedForUserCreation"])
        basic_bot_data = {
            "botList": basic_bot_list,
            "suggestPromptBot": _data["defaultPromptBotForUserCreation"]["botId"],
            "suggestImageBot": _data["defaultImageBotForUserCreation"]["botId"],
            "suggestVideoBot": _data["defaultVideoBotForUserCreation"]["botId"],
            "suggestRoleplayBot": _data["defaultRoleplayBotForUserCreation"]["botId"],
        }

        return basic_bot_data

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
                self.hashes["CreateKnowledgeSourceMutation"],
                file_list=files,
            )

        except Exception as e:
            raise Exception(f"上传bot引用资源失败: {repr(e)}")

        _data = result["data"]["knowledgeSourceCreate"]
        if _data["status"] != "success":
            if _data["status"] == "unsupported_file_type":
                raise UnsupportedFileType()

            if _data["status"] == "file_too_large":
                raise FileTooLarge()

            err_msg = _data["statusMessage"]
            raise Exception(f"上传bot引用资源失败: {err_msg}")

        _source = _data["source"]
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
                self.hashes["KnowledgeSourceModalFlowQuery"],
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
                self.hashes["EditKnowledgeSourceMutation"],
            )
        except Exception as e:
            raise Exception(f"编辑bot引用资源（仅限文本）失败: {repr(e)}")

        if result["data"]["knowledgeSourceEdit"]["status"] != "success":
            if (
                result["data"]["knowledgeSourceEdit"]["status"]
                == "unsupported_file_type"
            ):
                raise UnsupportedFileType()

            if result["data"]["knowledgeSourceEdit"]["status"] == "file_too_large":
                raise FileTooLarge()

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
            handle = generate_random_handle(20).lower()
            try:
                result = await self.send_query(
                    "CreateBotMain_poeBotCreate_Mutation",
                    {
                        "allowRelatedBotRecommendations": False,
                        "apiKey": generate_random_handle(32),
                        "apiUrl": None,
                        "baseBotId": baseBotId,
                        # "botCategory": 2,  # todo
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
                    self.hashes["PoeBotCreate"],
                )
            except Exception as e:
                raise Exception(f"创建bot失败: {repr(e)}")
            try:
                async with request(
                    "GET",
                    f"https://poe.com/_next/data/w4diyMjOxdjD6IZZxDJDt/{handle}.json?handle={handle}",
                    headers=self.headers,
                    timeout=ClientTimeout(5),
                    proxy=self.proxy,
                ) as response:
                    status_code = response.status
            except Exception:
                pass

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

    async def get_edit_bot_info(self, botName: str, botHandle) -> dict:
        """
        获取待编辑bot信息

        参数:
        - botName  bot名称
        - botHandle  bot Handle
        """
        try:
            _edit_bot_info = await self.send_query(
                "get_edit_bot_info",
                {"botName": botHandle},
                "",
            )
        except Exception as e:
            raise Exception(f"获取待编辑bot信息失败: {repr(e)}")

        basicBotViewer = _edit_bot_info["basicBotViewer"]
        basicBotData = {
            "botList": filter_basic_bot_info(
                basicBotViewer["botsAllowedForUserCreation"]
            ),
            "suggestPromptBot": basicBotViewer["defaultPromptBotForUserCreation"][
                "botId"
            ],
            "suggestImageBot": basicBotViewer["defaultImageBotForUserCreation"][
                "botId"
            ],
            "suggestVideoBot": basicBotViewer["defaultVideoBotForUserCreation"][
                "botId"
            ],
            "suggestRoleplayBot": basicBotViewer["defaultRoleplayBotForUserCreation"][
                "botId"
            ],
        }

        _bot_info = _edit_bot_info["botInfo"]
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
            for s in _bot_info["knowledgeSourceConnection"]["edges"]
        ]

        bot_info = {
            "basicBotData": basicBotData,
            "botInfo": {
                "botName": botName,
                "botId": _bot_info["botId"],
                "botHandle": _bot_info["handle"],
                "baseBotId": _bot_info["baseBotId"],
                "baseBotModel": _bot_info["model"],
                "description": _bot_info["description"],
                "prompt": _bot_info["promptPlaintext"],
                "citeSource": _bot_info["shouldCiteSources"],
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
                self.hashes["PoeBotEdit"],
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
                self.hashes["SendChatBreakMutation"],
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
                "useDeleteChat_deleteChat_Mutation",
                {"chatId": chat_id},
                self.hashes["DeleteChat"],
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
                "BotInfoCardActionBar_poeBotDelete_Mutation",
                {"botId": bot_id},
                self.hashes["PoeBotDelete"],
            )
        except Exception as e:
            raise Exception(f"bot {botName} 删除失败: {repr(e)}")

        if resp["data"] is None and resp["errors"]:
            raise Exception(f"bot {botName} 删除失败: {resp['errors'][0]['message']}")

    async def remove_bot(self, botName: str, bot_id: int):
        """
        从bot列表移除

        参数:
        - botName bot名称
        - bot_id bot id
        """
        try:
            resp = await self.send_query(
                "BotInfoCardActionBar_poeRemoveBotFromUserList_Mutation",
                {"botId": bot_id},
                self.hashes["PoeRemoveBotFromUserList"],
            )
        except Exception as e:
            raise Exception(f"bot {botName} 移除失败: {repr(e)}")

        if resp["data"] is None and resp["errors"]:
            raise Exception(f"bot {botName} 移除失败: {resp['errors'][0]['message']}")

    async def filter_bot_info(self, _bot_info: dict) -> dict:
        if "isOfficialBot" in _bot_info:
            if _bot_info["isOfficialBot"]:
                bot_type = "官方"
            elif _bot_info["isPrivateBot"]:
                bot_type = "自定义"
            else:
                bot_type = "第三方"
        else:
            if (
                "官方" in _bot_info["translatedBotTags"]
                or "OFFICIAL" in _bot_info["translatedBotTags"]
            ):
                bot_type = "官方"
            else:
                bot_type = "第三方"

        img_url = get_img_url(_bot_info["displayName"], _bot_info["picture"])

        try:
            # 尝试直接从结果解析（除了新会话都有的）
            standardPrice = _bot_info["botPricing"]["standardMessagePrice"]
            displayPrice = _bot_info["messagePointLimit"]["displayMessagePointPrice"]

            if not standardPrice:
                standardPrice = displayPrice

            self.bot_price_cache[_bot_info["nickname"]] = PriceCache(
                standardPrice=standardPrice, displayPrice=displayPrice
            )
            price = standardPrice
        except KeyError:
            # 如果没有，那就尝试从缓存拉，如果没有就从详情获取
            try:
                price = self.bot_price_cache[_bot_info["nickname"]].standardPrice
            except KeyError:
                await self.get_bot_info(_bot_info["displayName"])
                price = self.bot_price_cache[_bot_info["nickname"]].standardPrice

        bot_info = {
            "botName": _bot_info["displayName"],
            "botId": _bot_info["botId"],
            "botHandle": _bot_info["nickname"],
            "description": _bot_info["description"]
            if "description" in _bot_info
            else "",
            "allowImage": _bot_info["allowsImageAttachments"],
            "allowFile": _bot_info["supportsFileUpload"],
            "uploadFileSizeLimit": _bot_info["uploadFileSizeLimit"],
            "imgUrl": img_url,
            "price": price,
            "botType": bot_type,
            "canAccess": _bot_info["canUserAccessBot"],
        }
        return bot_info
