from io import BytesIO
from database import *
from models import *
from services import *
from utils import *
from utils.config import *


class BotNotFound(Exception):
    def __init__(self):
        pass


class NoChatCode(Exception):
    def __init__(self):
        pass


class ModelNotFound(Exception):
    def __init__(self, model: str):
        self.model = model


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    if "The bot doesn't exist or isn't accessible" in err_msg:
        return JSONResponse({"code": 3002, "msg": "该会话已失效，请创建新会话"}, 500)

    logger.error(err_msg)
    return JSONResponse({"code": 3001, "msg": err_msg}, 500)


available_model = set(poe.client.model_dict.keys())

router = APIRouter()


@router.post(
    "/create",
    summary="创建会话",
    responses={
        200: {
            "description": "创建成功",
            "content": {
                "application/json": {
                    "example": {"handle": "会话句柄"},
                }
            },
        },
    },
)
async def _(
    body: CreateBody = Body(
        example={
            "model": "ChatGPT",
            "prompt": "You are a large language model. Follow the user's instructions carefully.",
            "alias": "新会话",
        }
    ),
    user_data: dict = Depends(verify_token),
):
    if body.model not in available_model:
        raise ModelNotFound(body.model)

    user = user_data["user"]

    try:
        handle, bot_id = await poe.client.create_bot(
            body.model,
            body.prompt,
        )
        await Bot.create_bot(
            handle,
            bot_id,
            user,
            body.model,
            body.alias,
            body.prompt,
        )
        return JSONResponse({"handle": handle}, 200)

    except Exception as e:
        return handle_exception(str(e))


@router.post(
    "/{handle}/talk",
    summary="对话（提问）",
    responses={
        200: {
            "description": "回复内容",
            "content": {"text/plain": {"example": "你寄吧谁啊"}},
        }
    },
)
async def _(
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
    body: TalkBody = Body(example={"q": "你好啊"}),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    chat_id = await Bot.get_bot_chat_id(handle)

    async def ai_reply():
        async for data in poe.client.talk_to_bot(
            handle,
            chat_id,
            body.q,
        ):
            # 新的会话，需要保存chat code和chat id
            if isinstance(data, NewChat):
                await Bot.update_bot_chat_code_and_chat_id(
                    handle, data.chat_code, data.chat_id
                )
            # ai的回答
            if isinstance(data, Text):
                yield BytesIO(data.content.encode("utf-8")).read()
            # 回答完毕，更新最后对话时间
            if isinstance(data, End):
                await Bot.update_bot_last_talk_time(handle)
            # 出错
            if isinstance(data, TalkError):
                yield BytesIO(data.content.encode("utf-8")).read()

    return StreamingResponse(ai_reply(), media_type="text/plain")


@router.get(
    "/{handle}/stop",
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
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    chat_id = await Bot.get_bot_chat_id(handle)

    if not chat_id:
        raise NoChatCode()

    try:
        await poe.client.talk_stop(handle)
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.delete(
    "/{handle}",
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
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    bot_id = await Bot.get_bot_id(handle)

    try:
        await poe.client.delete_bot(handle, bot_id)
        await Bot.delete_bot(handle)
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.delete(
    "/{handle}/reset",
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
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    chat_id = await Bot.get_bot_chat_id(handle)

    if not chat_id:
        raise NoChatCode()

    try:
        await poe.client.send_chat_break(handle, chat_id)
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.delete(
    "/{handle}/clear",
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
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    chat_id = await Bot.get_bot_chat_id(handle)

    if not chat_id:
        raise NoChatCode()

    try:
        await poe.client.delete_chat_by_chat_id(handle, chat_id)
        await Bot.update_bot_chat_code_and_chat_id(handle)
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.get(
    "/{handle}/history/{cursor}",
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
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
    cursor: str = Path(description="光标，用于翻页，写0则从最新的拉取", example=0),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    chat_id = await Bot.get_bot_chat_id(handle)
    if not chat_id:
        raise NoChatCode()

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
    "/{handle}",
    summary="修改bot信息，不改的就不提交",
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
    handle: str = Path(description="会话句柄", example="t3JChplM0pgoNuGVEEyC"),
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
    if not await Bot.verify_bot(user, handle):
        raise BotNotFound()

    if body.model and body.model not in available_model:
        raise ModelNotFound(body.model)

    # 更新缓存
    await Bot.modify_bot(handle, body.model, body.alias, body.prompt)
    # 更新模型和预设
    if body.model or body.prompt:
        bot_id, _model, _prompt = await Bot.get_bot_botId_model_prompt(handle)
        try:
            await poe.client.edit_bot(
                handle,
                bot_id,
                body.model or _model,
                body.prompt or _prompt,
            )
        except Exception as e:
            return handle_exception(str(e))

    return Response(status_code=204)
