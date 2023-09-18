from io import BytesIO
from database import *
from models import *
from services import *
from utils import *
from utils.config import *
from time import strftime, localtime
from asyncio import create_task

try:
    from ujson import dumps
except:
    from json import dumps


class BotNotFound(Exception):
    def __init__(self):
        pass


class NoChat(Exception):
    def __init__(self):
        pass


class ModelNotFound(Exception):
    def __init__(self, model: str):
        self.model = model


class UserOutdate(Exception):
    def __init__(self, date: int):
        date_string = strftime("%Y-%m-%d %H:%M:%S", localtime(date / 1000))
        self.date = date_string


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    if "The bot doesn't exist or isn't accessible" in err_msg:
        return JSONResponse({"code": 3002, "msg": "该会话已失效，请创建新会话"}, 500)

    logger.error(err_msg)
    return JSONResponse({"code": 3001, "msg": err_msg}, 500)


async def check_bot_hoster(user: str, eop_id: str):
    if not await Bot.check_bot_user(eop_id, user):
        raise BotNotFound()


async def check_chat_exist(id: int):
    if not id:
        raise NoChat()


router = APIRouter()


@router.get(
    "/models",
    summary="获取可用模型",
    responses={
        200: {
            "description": "diy指是否可以设置prompt，limited指是否有使用次数限制",
            "content": {
                "application/json": {
                    "example": {
                        "available_models": [
                            {
                                "model": "ChatGPT",
                                "description": "由gpt-3.5-turbo驱动。",
                                "diy": True,
                                "limited": False,
                            },
                            {
                                "model": "GPT-4",
                                "description": "OpenAI最强大的模型。在定量问题（数学和物理）、创造性写作和许多其他具有挑战性的任务方面比ChatGPT更强大。",
                                "diy": True,
                                "limited": True,
                            },
                            {
                                "model": "Google-PaLM",
                                "description": "由Google的PaLM 2 chat-bison-001模型驱动。",
                                "diy": False,
                                "limited": False,
                            },
                        ]
                    },
                }
            },
        },
    },
)
async def _(
    _: dict = Depends(verify_token),
):
    model_list, next_cursor = await poe.client.explore_bot("Official")
    for m in model_list:
        if m not in poe.client.offical_models:
            try:
                await poe.client.cache_offical_bot_info(m)
            except Exception as e:
                return handle_exception(str(e))

    data = []
    for model in model_list:
        info = poe.client.offical_models[model]
        data.append(
            {
                "model": model,
                "description": info.description,
                "diy": info.diy,
                "limited": info.limited,
            }
        )
    return JSONResponse({"available_models": data}, 200)


@router.get(
    "/limited",
    summary="获取限制模型的使用情况",
    responses={
        200: {
            "description": "结果",
            "content": {
                "application/json": {
                    "example": {
                        "notice": "订阅会员才有的，软限制就是次数用完后会降低生成质量和速度，硬限制就是用完就不能生成了",
                        "models": [
                            {
                                "model": "Claude-instant-100k",
                                "limit_type": "硬限制",
                                "available": True,
                                "daily_available_times": 30,
                                "daily_total_times": 30,
                                "monthly_available_times": 1030,
                                "monthly_total_times": 1030,
                            },
                            {
                                "model": "GPT-4",
                                "limit_type": "软限制",
                                "available": True,
                                "daily_available_times": 1,
                                "daily_total_times": 1,
                                "monthly_available_times": 592,
                                "monthly_total_times": 601,
                            },
                        ],
                        "daily_refresh_time": "2023-08-30 08:00:00",
                        "monthly_refresh_time": "2023-09-13 08:00:00",
                    },
                }
            },
        },
    },
)
async def _(
    _: dict = Depends(verify_token),
):
    data = await poe.client.get_limited_bots_info()
    return JSONResponse(data, 200)


@router.post(
    "/create",
    summary="创建会话，prompt选填（不填留空），prompt仅支持diy的模型可用",
    responses={
        200: {
            "description": "创建成功",
            "content": {
                "application/json": {
                    "bot_info": {
                        "eop_id": "114514",
                        "alias": "AAA",
                        "model": "ChatGPT",
                        "prompt": "prompt_A",
                        "image": "https://xxx",
                        "create_time": 1693230928703,
                        "last_talk_time": 1693230928703,
                    },
                }
            },
        },
    },
)
async def _(
    body: CreateBody = Body(
        example={
            "model": "ChatGPT",
            "prompt": "",
            "alias": "新会话",
        }
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]

    if await User.is_outdate(user):
        expire_date = await User.get_expire_date(user)
        raise UserOutdate(expire_date)

    if body.model not in poe.client.offical_models:
        raise ModelNotFound(body.model)

    can_diy = poe.client.offical_models[body.model].diy

    try:
        # 如果是自定义prompt需要创建新的bot
        if can_diy and body.prompt:
            handle, bot_id = await poe.client.create_bot(
                poe.client.offical_models[body.model].model, body.prompt
            )
            can_diy = True
        else:
            handle, bot_id = (
                poe.client.offical_models[body.model].model,
                poe.client.offical_models[body.model].bot_id,
            )
            can_diy = False

        # 获取bot头像
        bot_data = await poe.client.get_bot_info(body.model)
        image_link = bot_data["image_link"]
        eop_id = await Bot.create_bot(
            can_diy,
            handle,
            bot_id,
            user,
            body.model,
            body.alias,
            body.prompt,
            image_link,
        )
        user_logger.info(f"用户:{user}  动作:创建会话  eop_id:{eop_id}  handle:{handle}")
        bot_info = await Bot.get_user_bot(user)
        return JSONResponse({"bot_info": bot_info[0]}, 200)

    except Exception as e:
        return handle_exception(str(e))


@router.post(
    "/{eop_id}/talk",
    summary="对话（提问）",
    responses={
        200: {
            "description": "回复内容，完毕type为end，出错type为error",
            "content": {
                "application/json": {
                    "example": {
                        "type": "response",
                        "data": "回答内容",
                    }
                }
            },
        }
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    body: TalkBody = Body(example={"q": "你好啊"}),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if await User.is_outdate(user):
        expire_date = await User.get_expire_date(user)
        raise UserOutdate(expire_date)

    await check_bot_hoster(user, eop_id)

    handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)

    async def ai_reply():
        nonlocal chat_id
        async for data in poe.client.talk_to_bot(handle, chat_id, body.q):
            # 次数上限，有效性待测试
            if isinstance(data, ReachedLimit):
                yield BytesIO(
                    (dumps({"type": "limited", "data": "该模型使用次数已耗尽"}) + "\n").encode(
                        "utf-8"
                    )
                ).read()
            # 新的会话，需要保存chat code和chat id
            if isinstance(data, NewChat):
                chat_id = data.chat_id
                user_logger.info(
                    f"用户:{user}  动作:新会话  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
                )
                await Bot.update_bot_chat_id(eop_id, chat_id)
            # 对话消息id和创建时间，用于同步
            if isinstance(data, MsgId):
                await Bot.update_bot_last_talk_time(eop_id, data.answer_create_time)
                yield BytesIO(
                    (
                        dumps(
                            {
                                "type": "start",
                                "data": {
                                    "question_msg_id": data.question_msg_id,
                                    "question_create_time": data.question_create_time,
                                    "answer_msg_id": data.answer_msg_id,
                                    "answer_create_time": data.answer_create_time,
                                },
                            }
                        )
                        + "\n"
                    ).encode("utf-8")
                ).read()
            # ai的回答
            if isinstance(data, Text):
                yield BytesIO(
                    (dumps({"type": "response", "data": data.content}) + "\n").encode(
                        "utf-8"
                    )
                ).read()
            # 回答完毕，更新最后对话时间
            if isinstance(data, End):
                user_logger.info(
                    f"用户:{user}  动作:回答完毕  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
                )
                yield BytesIO((dumps({"type": "end"}) + "\n").encode("utf-8")).read()
            # 出错
            if isinstance(data, TalkError):
                user_logger.error(
                    f"用户:{user}  动作:回答出错  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
                )
                # 切换ws channel地址
                create_task(poe.client.refresh_channel())
                yield BytesIO(
                    (dumps({"type": "error", "data": data.content}) + "\n").encode(
                        "utf-8"
                    )
                ).read()

    return StreamingResponse(ai_reply(), media_type="text/event-stream")


@router.get(
    "/{eop_id}/stop",
    summary="停止生成回答",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "停止成功",
        },
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await check_bot_hoster(user, eop_id)

    handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
    await check_chat_exist(chat_id)

    try:
        await poe.client.talk_stop(handle, chat_id)
        user_logger.info(
            f"用户:{user}  动作:停止回答  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
        )
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.delete(
    "/{eop_id}",
    summary="删除会话",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "删除成功",
        },
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await check_bot_hoster(user, eop_id)

    handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)

    try:
        if await Bot.bot_can_diy(eop_id):
            handle, bot_id = await Bot.get_handle_and_bot_id(eop_id)
            if chat_id:
                await poe.client.delete_chat_by_chat_id(handle, chat_id)
            await poe.client.delete_bot(handle, bot_id)

        else:
            handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
            if chat_id:
                await poe.client.delete_chat_by_chat_id(handle, chat_id)

    except Exception as e:
        return handle_exception(str(e))

    await Bot.delete_bot(eop_id)
    user_logger.info(
        f"用户:{user}  动作:删除会话  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
    )
    return Response(status_code=204)


@router.delete(
    "/{eop_id}/reset",
    summary="重置对话，仅清除bot记忆，不会删除聊天记录",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "重置成功",
        },
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await check_bot_hoster(user, eop_id)

    handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
    await check_chat_exist(chat_id)

    try:
        await poe.client.send_chat_break(handle, chat_id)
        user_logger.info(
            f"用户:{user}  动作:重置对话  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
        )
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.delete(
    "/{eop_id}/clear",
    summary="重置对话并删除聊天记录",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "重置成功",
        },
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await check_bot_hoster(user, eop_id)

    handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
    await check_chat_exist(chat_id)

    try:
        await poe.client.delete_chat_by_chat_id(handle, chat_id)
        await Bot.update_bot_chat_id(eop_id)
        user_logger.info(
            f"用户:{user}  动作:重置对话并删除聊天记录  eop_id:{eop_id}  handle:{handle}  chat_id:{chat_id}"
        )
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.get(
    "/{eop_id}/history/{cursor}",
    summary="拉取聊天记录",
    responses={
        200: {
            "description": "返回历史记录和翻页光标，如果next_cursor为-1，则没有下一页",
            "content": {
                "application/json": {
                    "example": {
                        "history": [
                            {
                                "msg_id": 2692997857,
                                "create_time": 1692964266475260,
                                "text": "你好啊",
                                "author": "user",
                            },
                            {
                                "msg_id": 2692997880,
                                "create_time": 1692964266638975,
                                "text": "你好啊！我是你的智能助手。有什么我可以帮助你的吗？",
                                "author": "bot",
                            },
                        ],
                        "next_cursor": "2692997857",
                    }
                }
            },
        }
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    cursor: str = Path(description="光标，用于翻页，写0则从最新的拉取", example=0),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await check_bot_hoster(user, eop_id)

    handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
    if not chat_id:
        return JSONResponse(
            {
                "history": [],
                "next_cursor": -1,
            },
            200,
        )

    try:
        result_list, next_cursor = await poe.client.get_chat_history(
            handle, chat_id, cursor
        )

        return JSONResponse(
            {
                "history": result_list,
                "next_cursor": next_cursor,
            },
            200,
        )

    except Exception as e:
        return handle_exception(str(e))


@router.patch(
    "/{eop_id}",
    summary="修改bot信息，不改的就不提交，prompt如果为空的会话只能修改alias",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "成修改功",
        },
    },
)
async def _(
    eop_id: str = Path(description="会话唯一标识", example="114514"),
    body: ModifyBotBody = Body(
        example={
            "alias": "智能傻逼",
            "model": "ChatGPT",
            "prompt": "You are a large language model. Follow the user's instructions carefully.",
        }
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await check_bot_hoster(user, eop_id)

    if body.model and body.model not in poe.client.offical_models:
        raise ModelNotFound(body.model)

    # 更新缓存
    await Bot.modify_bot(eop_id, None, body.alias, None)

    # 只有支持diy的可以更新模型和预设
    if await Bot.bot_can_diy(eop_id) and (body.model or body.prompt):
        # 更新缓存
        await Bot.modify_bot(eop_id, body.model, None, body.prompt)
        handle, bot_id, _model, _prompt = await Bot.get_bot_handle_botId_model_prompt(
            eop_id
        )
        try:
            await poe.client.edit_bot(
                handle,
                bot_id,
                poe.client.offical_models[body.model or _model].model,
                body.prompt or _prompt,
            )
        except Exception as e:
            return handle_exception(str(e))

    return Response(status_code=204)


@router.get(
    "/explore/{cursor}",
    summary="探索bot",
    responses={
        200: {
            "description": "返回历史记录和翻页光标，如果next_cursor为-1，则没有下一页",
            "content": {
                "application/json": {
                    "example": {
                        "history": [
                            {
                                "msg_id": 2692997857,
                                "create_time": 1692964266475260,
                                "text": "你好啊",
                                "author": "user",
                            },
                            {
                                "msg_id": 2692997880,
                                "create_time": 1692964266638975,
                                "text": "你好啊！我是你的智能助手。有什么我可以帮助你的吗？",
                                "author": "bot",
                            },
                        ],
                        "next_cursor": "2692997857",
                    }
                }
            },
        }
    },
)
async def _(
    cursor: str = Path(description="光标，用于翻页，写0则从最新的拉取", example=0),
    _: dict = Depends(verify_token),
):
    # handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
    # if not chat_id:
    #     return JSONResponse(
    #         {
    #             "history": [],
    #             "next_cursor": -1,
    #         },
    #         200,
    #     )

    # try:
    #     result_list, next_cursor = await poe.client.get_chat_history(
    #         handle, chat_id, cursor
    #     )

    #     return JSONResponse(
    #         {
    #             "history": result_list,
    #             "next_cursor": next_cursor,
    #         },
    #         200,
    #     )

    # except Exception as e:
    #     return handle_exception(str(e))
    pass
