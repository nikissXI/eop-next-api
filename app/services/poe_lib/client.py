from asyncio import Queue, TimeoutError, create_task, sleep, wait_for, gather
from hashlib import md5
from random import randint
from secrets import token_hex
from time import localtime, strftime
from traceback import format_exc
from typing import AsyncGenerator
from uuid import UUID, uuid5
from httpx import AsyncClient
from websockets.client import connect as ws_connect
from re import sub
from .type import *
from .util import (
    GQL_URL,
    SETTING_URL,
    BOT_IMAGE_LINK_CACHE,
    CHINESE_DISCRIPTION,
    base64_decode,
    base64_encode,
    generate_data,
    generate_random_handle,
)

try:
    from ujson import dump, loads
except:
    from json import dump, loads
try:
    from utils import logger, refresh_logger
except:
    from loguru import logger


class Poe_Client:
    def __init__(self, p_b: str, formkey: str, proxy: str | None = None):
        self.formkey = formkey
        self.p_b = p_b
        self.sdid = ""
        self.user_info = UserInfo()
        self.offical_models: dict[str, ModelInfo] = {}
        self.category_list: list[str] = []
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
            "Origin": "https://poe.com",
            "Referer": "https://poe.com",
        }
        self.httpx_client = AsyncClient(headers=headers, proxies=proxy)
        self.channel_url = ""
        self.ws_client_task = None
        self.refresh_channel_lock = False
        self.last_min_seq = 0
        self.ws_data_queue: dict[int, Queue] = {}
        self.get_chat_code = {}
        self.answer_msg_id_cache = {}
        self.last_text_len_cache = {}

    async def login(self):
        """
        创建poe请求实例，可用于验证凭证是否有效，并拉取用户数据。
        """
        if not (self.p_b and self.formkey):
            raise Exception(f"p_b和formkey未正确填写，不登陆")

        logger.info("Poe登陆中。。。。。。")

        await self.get_user_info()
        text = f"\n账号信息\n -- 邮箱：{self.user_info.email}\n -- 购买订阅：{self.user_info.subscription_actived}"
        if self.user_info.subscription_actived:
            text += f"\n -- 订阅类型：{self.user_info.plan_type}\n -- 到期时间：{self.user_info.expire_time}"
        logger.info(text)

        limited_info = await self.get_limited_bots_info()
        text = f"\n有次数限制bot的使用情况\n -- 日次数刷新时间：{limited_info['daily_refresh_time']}"
        if self.user_info.subscription_actived:
            text += f"\n -- 月次数刷新时间：{limited_info['monthly_refresh_time']}"
        for m in limited_info["models"]:
            text += f"\n >> 模型：{m['model']}\n    {m['limit_type']}  可用：{m['available']}  日可用次数：{m['daily_available_times']}/{m['daily_total_times']}"
            if self.user_info.subscription_actived:
                text += (
                    f"  月可用次数：{m['monthly_available_times']}/{m['monthly_total_times']}"
                )
        logger.info(text)

        # 获取官方模型
        await self.cache_offical_models()

        # 取消之前的ws连接
        if self.ws_client_task:
            self.ws_client_task.cancel()
        create_task(self.refresh_channel())

        return self

    async def get_user_info(self):
        """
        获取账号信息
        """
        try:
            result = await self.send_query("settingsPageQuery", {})
            data = result["data"]["viewer"]
            self.sdid = str(
                uuid5(UUID("98765432101234567898765432101234"), data["poeUser"]["id"])
            )
            self.user_info.email = data["primaryEmail"]
            self.user_info.subscription_actived = data["subscription"]["isActive"]
            if self.user_info.subscription_actived:
                self.user_info.plan_type = data["subscription"]["planType"]
                self.user_info.expire_time = strftime(
                    "%Y-%m-%d %H:%M:%S",
                    localtime(data["subscription"]["expiresTime"] / 1000000),
                )
        except Exception as e:
            raise e

    async def explore_bot(self, category: str) -> tuple[list[str], str]:
        """
        获取某个会话的历史记录

        参数:
        - category 类别名称
        """
        handle_list = []
        next_cursor = "0"
        while True:
            result = await self.send_query(
                "ExploreBotsListPaginationQuery",
                {
                    "categoryName": category,
                    "count": 25,
                    "cursor": next_cursor,
                },
            )
            data = result["data"]["exploreBotsConnection"]
            handle_list.extend([m["node"]["handle"] for m in data["edges"]])

            # for m in data["edges"]:
            #     handle: str = m["node"]["handle"]
            #     bot_id: int = m["node"]["botId"]
            #     description: str = m["node"]["description"]
            #     if m["node"]["image"]["__typename"] == "UrlBotImage":
            #         image_link: str = m["node"]["image"]["url"]
            #     elif handle in BOT_IMAGE_LINK_CACHE:
            #         image_link = BOT_IMAGE_LINK_CACHE[handle]
            #     else:
            #         raise Exception("image_link不存在")

            if data["pageInfo"]["hasNextPage"]:
                next_cursor: str = data["pageInfo"]["endCursor"]
            else:
                next_cursor = "-1"

            # 如果获取官方模型信息就拉全部（因为数量有限）
            if category == "Official" and data["pageInfo"]["hasNextPage"]:
                continue
            else:
                break

        return handle_list, next_cursor

    async def cache_offical_models(self):
        """
        缓存官方模型信息
        """
        try:
            # 获取category可选项
            result = await self.send_query(
                "exploreBotsIndexPageQuery",
                {"categoryName": "Official"},
            )

            self.category_list = [
                c["categoryName"] for c in result["data"]["exploreBotsCategoryObjects"]
            ]

            # 获取支持diy（create bot）的模型
            result = await self.send_query(
                "createBotIndexPageQuery",
                {"messageId": None},
            )
            diy_model_list: list[str] = [
                _["displayName"]
                for _ in result["data"]["viewer"]["botsAllowedForUserCreation"]
            ]

            # 获取详细信息
            handle_list, _ = await self.explore_bot("Official")
            task_list = [self.cache_offical_bot_info(handle) for handle in handle_list]
            await gather(*task_list)

            # 标记可创建自定义bot的模型
            for m in diy_model_list:
                self.offical_models[m].diy = True

            logger.info(f"当前发现{len(handle_list)}个官方模型：" + "、".join(handle_list))
        except Exception as e:
            raise e

    async def cache_offical_bot_info(self, handle: str):
        """
        缓存官方bot详细信息
        """
        try:
            result = await self.send_query(
                "HandleBotLandingPageQuery",
                {"botHandle": handle},
            )

            info: dict = result["data"]["bot"]
            if info["displayName"] in CHINESE_DISCRIPTION:
                description = CHINESE_DISCRIPTION[info["displayName"]]
            else:
                logger.warning(f"模型{info['displayName']}的介绍未作汉化")
                description = info["description"]
            self.offical_models[info["displayName"]] = ModelInfo(
                model=info["model"],
                description=description,
                diy=False,
                limited=False if info["limitedAccessType"] == "no_limit" else True,
                bot_id=info["botId"],
            )
        except Exception as e:
            raise e

    async def get_bot_info(self, handle: str) -> dict:
        """
        获取bot详细信息
        """
        try:
            result = await self.send_query(
                "HandleBotLandingPageQuery",
                {"botHandle": handle},
            )
            info: dict = result["data"]["bot"]

            if info["image"]["__typename"] == "UrlBotImage":
                image_link = info["image"]["url"]
            elif handle in BOT_IMAGE_LINK_CACHE:
                image_link = BOT_IMAGE_LINK_CACHE[handle]
            else:
                image_link = ""

            bot_info = {
                "bot_id": info["botId"],
                "handle": info["nickname"],
                "displayName": info["displayName"],
                "image_link": image_link,
            }
            return bot_info
        except Exception as e:
            raise e

    async def get_limited_bots_info(self) -> dict:
        """
        获取有次数限制bot的使用情况
        """
        try:
            result = await self.send_query("settingsPageQuery", {})
            data = result["data"]["viewer"]["subscriptionBots"]
            output = {
                "notice": "订阅会员才有的，软限制就是次数用完后会降低生成质量和速度，硬限制就是用完就不能生成了",
                "models": [],
            }
            for m in data:
                output["daily_refresh_time"] = m["messageLimit"]["resetTime"]
                daily_available_times = m["messageLimit"]["dailyBalance"]
                daily_total_times = m["messageLimit"]["dailyLimit"]

                tmp_data = {
                    "model": m["displayName"],
                    "limit_type": "软限制"
                    if m["limitedAccessType"] == "soft_limit"
                    else "硬限制",
                    "available": m["messageLimit"]["canSend"],
                    "daily_available_times": daily_available_times,
                    "daily_total_times": daily_total_times,
                }
                if self.user_info.subscription_actived:
                    output["monthly_refresh_time"] = m["messageLimit"][
                        "monthlyBalanceRefreshTime"
                    ]
                    monthly_available_times = m["messageLimit"]["monthlyBalance"]
                    monthly_total_times = m["messageLimit"]["monthlyLimit"]
                    tmp_data.update(
                        {
                            "monthly_available_times": monthly_available_times,
                            "monthly_total_times": monthly_total_times,
                        }
                    )
                output["models"].append(tmp_data)

            output["daily_refresh_time"] = strftime(
                "%Y-%m-%d %H:%M:%S",
                localtime(output["daily_refresh_time"] / 1000000),
            )
            if self.user_info.subscription_actived:
                output["monthly_refresh_time"] = strftime(
                    "%Y-%m-%d %H:%M:%S",
                    localtime(output["monthly_refresh_time"] / 1000000),
                )
            return output
        except Exception as e:
            raise e

    async def send_query(self, query_name: str, variables: dict) -> dict:
        """
        发送请求
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
                if err_msg == "Server Error":
                    raise ServerError()
                else:
                    logger.error(resp.status_code)
                    logger.error(resp.text)
                    raise Exception(resp.text)

            return json_data
        except ServerError:
            raise ServerError("server error")
        except Exception as e:
            # with open("error.json", "a") as a:
            #     a.write(resp.text + "\n")  # type: ignore
            raise Exception(f"执行请求【{query_name}】失败，错误信息：{e}")

    async def create_bot(self, model: str, prompt: str) -> tuple[str, int]:
        """
        创建bot
        """
        while True:
            handle = generate_random_handle()
            result = await self.send_query(
                "CreateBotMain_poeBotCreate_Mutation",
                {
                    "handle": handle,
                    "prompt": prompt,
                    "model": model,
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
                    "isPrivateBot": True,
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

    async def get_new_channel(self):
        """
        此函数从设置_URL获取通道数据，获取channel地址，对话用的
        """
        self.ws_data_queue.clear()
        self.get_chat_code.clear()
        self.answer_msg_id_cache.clear()
        try:
            resp = await self.httpx_client.get(SETTING_URL)
            json_data = loads(resp.text)

            tchannel_data = json_data["tchannelData"]
            self.httpx_client.headers["Poe-Tchannel"] = tchannel_data["channel"]
            ws_domain = f"tch{randint(1, int(1e6))}"[:8]
            self.channel_url = f'wss://{ws_domain}.tch.{tchannel_data["baseHost"]}/up/{tchannel_data["boxName"]}/updates?min_seq={tchannel_data["minSeq"]}&channel={tchannel_data["channel"]}&hash={tchannel_data["channelHash"]}'
            self.last_min_seq = int(tchannel_data["minSeq"])
        except Exception as e:
            err_msg = f"获取channel address失败，错误信息：{e}"
            logger.error(err_msg)
            raise Exception(err_msg)

        try:
            await self.send_query(
                "subscriptionsMutation",
                {
                    "subscriptions": [
                        {
                            "query": None,
                            "queryHash": "4388f77d26d4fdf99ef6b0c2eaaddbc8f2de2785bb377bb318664144538dbeb5",
                            "subscriptionName": "messageAdded",
                        },
                        {
                            "query": None,
                            "queryHash": "dfcedd9e0304629c22929725ff6544e1cb32c8f20b0c3fd54d966103ccbcf9d3",
                            "subscriptionName": "messageCancelled",
                        },
                        {
                            "query": None,
                            "queryHash": "91f1ea046d2f3e21dabb3131898ec3c597cb879aa270ad780e8fdd687cde02a3",
                            "subscriptionName": "messageDeleted",
                        },
                        {
                            "query": None,
                            "queryHash": "ee640951b5670b559d00b6928e20e4ac29e33d225237f5bdfcb043155f16ef54",
                            "subscriptionName": "viewerStateUpdated",
                        },
                        {
                            "query": None,
                            "queryHash": "80ccbe90cb2eb8f10c9847ce5bf05cb7f568c38f30e5e070f3d20c1dff02621a",
                            "subscriptionName": "messageLimitUpdated",
                        },
                        {
                            "query": None,
                            "queryHash": "8affa725ade31d757a31e9903e0c5d8759129829baab79c39732cdaa9cc4dde8",
                            "subscriptionName": "chatTitleUpdated",
                        },
                    ]
                },
            )
        except Exception as e:
            raise Exception(f"subscribe执行失败，错误信息：{e}")

    async def refresh_channel(self, get_new_channel: bool = True):
        """
        刷新ws连接
        """
        self.refresh_channel_lock = True

        if get_new_channel:
            await self.get_new_channel()
        else:
            self.channel_url = sub(
                r"(min_seq=)\d+",
                r"\g<1>" + str(self.last_min_seq),
                self.channel_url,
            )

        # 取消之前的ws连接
        if self.ws_client_task:
            self.ws_client_task.cancel()
        # 创建新的ws连接任务
        self.ws_client_task = create_task(self.connect_to_channel())
        # 解除锁定
        self.refresh_channel_lock = False

    async def handle_ws_data(self, ws_data: dict):
        """
        处理ws中的数据
        """
        # 更新min_seq
        min_seq = ws_data.get("min_seq")
        if min_seq and min_seq > self.last_min_seq:
            self.last_min_seq: int = min_seq

        if "error" in ws_data.keys() and ws_data["error"] == "missed_messages":
            create_task(self.refresh_channel())
            return

        data_list: list[dict] = [
            loads(msg_str) for msg_str in ws_data.get("messages", "{}")
        ]
        for data in data_list:
            message_type = data.get("message_type")
            if message_type == "refetchChannel":
                create_task(self.refresh_channel())
                return

            payload = data.get("payload", {})

            if payload.get("subscription_name") not in [
                "messageAdded",
                "messageCancelled",
            ]:
                continue

            data = (payload.get("data", {})).get("messageAdded", {})
            # 去掉空内容和带建议的
            if not data or data["suggestedReplies"]:
                continue

            chat_id: int = int(payload.get("unique_id")[13:])

            if self.get_chat_code and data.get("author") == "human":
                question_md5 = md5(data.get("text").encode()).hexdigest()
                if question_md5 in self.get_chat_code:
                    self.get_chat_code[question_md5] = chat_id

            # 如果不存在则创建答案生成队列
            if chat_id not in self.ws_data_queue:
                self.ws_data_queue[chat_id] = Queue()

            await self.ws_data_queue[chat_id].put(data)

    async def connect_to_channel(self):
        """
        连接到poe的websocket，用于拉取回答
        """
        async with ws_connect(self.channel_url) as ws:
            while True:
                try:
                    data = await wait_for(ws.recv(), 120)
                    # with open("wss.json", "a") as a:
                    #     a.write(str(data) + "\n\n")  # type: ignore
                    await self.handle_ws_data(loads(data))

                except TimeoutError:
                    # logger.info("TimeoutError")
                    refresh_logger.info("refresh")
                    create_task(self.refresh_channel(get_new_channel=False))
                    break

                except Exception as e:
                    print(format_exc())
                    logger.error(f"ws channel连接出错：{repr(e)}")
                    with open("error.json", "a") as a:
                        a.write(str(data) + "\n")  # type: ignore
                    create_task(self.refresh_channel(get_new_channel=True))
                    break

    async def talk_to_bot(
        self, handle: str, chat_id: int, question: str
    ) -> AsyncGenerator:
        """
        向指定的机器人发送问题
        """
        # channel地址刷新中
        while self.refresh_channel_lock:
            await sleep(1)

        question_md5 = ""
        if not chat_id:
            question_md5 = md5(question.encode()).hexdigest()
            self.get_chat_code[question_md5] = 0

        try:
            resp = await self.send_query(
                "sendMessageMutation",
                {
                    "attachments": [],
                    "bot": handle,
                    "chatId": chat_id if chat_id else None,
                    "clientNonce": token_hex(8),
                    "query": question,
                    "sdid": self.sdid,
                    "shouldFetchChat": False if chat_id else True,
                    "source": {
                        "chatInputMetadata": {"useVoiceRecord": False},
                        "sourceType": "chat_input",
                    },
                },
            )
            # 次数上限，有效性待测试
            if resp["data"]["messageEdgeCreate"]["status"] == "reached_limit":
                yield ReachedLimit()
                return
        except ServerError:
            pass
        except Exception as e:
            err_msg = f"执行bot【{handle}】chat【{chat_id}】发送问题出错，错误信息：{e}"
            # print(format_exc())
            logger.error(err_msg)

        # 如果不存在则创建答案生成队列
        if chat_id and chat_id not in self.ws_data_queue:
            self.ws_data_queue[chat_id] = Queue()

        question_msg_id = 0
        question_create_time = 0

        yield_msg_id = False
        retry = 10
        while retry >= 0:
            if not chat_id:
                await sleep(1)
                if self.get_chat_code[question_md5]:
                    chat_id = self.get_chat_code[question_md5]
                    self.get_chat_code.pop(question_md5)
                    yield NewChat(chat_id=chat_id)
                    retry = 10

                    if chat_id not in self.ws_data_queue:
                        self.ws_data_queue[chat_id] = Queue()
                else:
                    retry -= 1
                continue

            # 从队列拉取回复
            try:
                quene_data = await wait_for(self.ws_data_queue[chat_id].get(), 2)
            except TimeoutError:
                retry -= 1
                continue

            # 获取问题的msg id和creation time
            if quene_data.get("author") == "human":
                question_msg_id: int = quene_data.get("messageId")
                question_create_time: int = quene_data.get("creationTime")
                continue

            # 收到第一条生成的回复
            if yield_msg_id == False:
                answer_msg_id = quene_data.get("messageId")
                # 判断是否为旧消息，有时候会拉取到之前的消息
                if (
                    chat_id in self.answer_msg_id_cache
                    and answer_msg_id <= self.answer_msg_id_cache[chat_id]
                ):
                    continue
                answer_create_time = quene_data.get("creationTime")

                self.answer_msg_id_cache[chat_id] = answer_msg_id
                self.last_text_len_cache[chat_id] = 0
                yield MsgId(
                    question_msg_id=question_msg_id,
                    question_create_time=question_create_time,
                    answer_msg_id=answer_msg_id,
                    answer_create_time=answer_create_time,
                )
                yield_msg_id = True

            # 取消回复
            if quene_data.get("state") == "cancelled":
                yield End()
                return

            # 获取内容
            plain_text = quene_data.get("text")

            # 未完成的回复
            if quene_data.get("state") == "incomplete":
                retry = 10
                yield Text(content=plain_text[self.last_text_len_cache[chat_id] :])
                self.last_text_len_cache[chat_id] = len(plain_text)
                continue

            # 完成回复
            if (
                quene_data.get("state") == "complete"
                or quene_data.get("state") == "cancelled"
            ):
                yield Text(content=plain_text[self.last_text_len_cache[chat_id] :])
                yield End()
                return

        err_msg = "获取回答超时"
        logger.error(err_msg)
        yield TalkError(content=err_msg)
        return

    async def talk_stop(self, handle: str, chat_id: int):
        """
        停止生成回复
        """
        if (
            chat_id not in self.answer_msg_id_cache
            or chat_id not in self.last_text_len_cache
        ):
            return

        msg_id = self.answer_msg_id_cache[chat_id]
        try:
            await self.send_query(
                "chatHelpers_messageCancel_Mutation",
                {
                    "linkifiedTextLength": self.last_text_len_cache[chat_id],
                    "messageId": msg_id,
                    "textLength": self.last_text_len_cache[chat_id],
                },
            )
        except Exception as e:
            raise Exception(f"停止bot【{handle}】生成回答失败，错误信息：{e}")

    async def edit_bot(self, handle: str, bot_id: int, model: str, prompt: str):
        """
        编辑bot设置
        """
        result = await self.send_query(
            "EditBotMain_poeBotEdit_Mutation",
            {
                "prompt": prompt,
                "baseBot": model,
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
                "isPrivateBot": True,
                "temperature": None,
            },
        )

        data = result["data"]["poeBotEdit"]
        if data["status"] != "success":
            raise Exception(f"编辑bot失败，错误信息：{data['status']}")

    async def send_chat_break(self, handle: str, chat_id: int):
        """
        重置对话，仅清除会话记忆，不会删除聊天记录。
        """
        try:
            await self.send_query(
                "sendChatBreakMutation",
                {
                    "chatId": chat_id,
                    "clientNonce": token_hex(8),
                },
            )
        except Exception as e:
            raise Exception(f"bot【{handle}】重置对话失败，错误信息：{e}")

    async def delete_chat_by_chat_id(self, handle: str, chat_id: int):
        """
        删除某个bot下的会话
        """
        try:
            await self.send_query(
                "useDeleteChat_deleteChat_Mutation", {"chatId": chat_id}
            )
        except Exception as e:
            raise Exception(f"删除chat【{handle}】失败，错误信息：{e}")

    async def delete_bot(self, handle: str, bot_id: int):
        """
        删除bot
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
        - handle 要发送聊天终止信号的机器人的唯一标识符
        - chat_id 与机器人的聊天的唯一标识符
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

            # 没有聊天记录
            if result["data"]["node"] == None:
                return [], "-1"

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
                if n["author"] == "chat_break":
                    continue
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
