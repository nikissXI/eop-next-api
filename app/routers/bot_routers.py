from hashlib import sha256
from io import BytesIO
from database import *
from models import *
from services import *
from utils import *
from utils.config import *


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    if "The bot doesn't exist or isn't accessible" in err_msg:
        return JSONResponse({"code": 6000, "msg": "该会话已失效，请创建新会话"}, 500)

    logger.error(err_msg)
    return JSONResponse({"code": 6000, "msg": err_msg}, 500)


router = APIRouter()


@router.post("/create", summary="创建会话")
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
    model_dict = {
        "ChatGPT": "chinchilla",
        "Claude": "a2",
        "ChatGPT4": "beaver",
        "Claude-2-100k": "a2_2",
    }

    if body.model not in model_dict:
        return JSONResponse(
            {
                "code": 2000,
                "msg": "Available model: ChatGPT, Claude, ChatGPT4, Claude-2-100k.",
            },
            402,
        )

    user = user_data["user"]

    while True:
        try:
            bot_id = generate_random_bot_id()
            await poe.client.create_bot(
                handle=bot_id,
                prompt=body.prompt,
                base_model=model_dict[body.model],
                suggested_replies=False,
            )
            await User.add_user_botId(user, bot_id, body.alias)
            return JSONResponse({"code": 2000, "bot_id": bot_id}, 200)

        except Exception as e:
            return handle_exception(str(e))


@router.post("/{bot_id}/talk", summary="对话（提问）")
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    body: TalkBody = Body(example={"q": "你好啊"}),
    _: dict = Depends(verify_token),
):
    try:

        async def generate():
            async for message in poe.client.ask_stream(
                url_botname=bot_id,
                question=body.q,
                suggest_able=False,
            ):
                yield BytesIO(message.encode("utf-8")).read()

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        return handle_exception(str(e))


@router.delete("/{bot_id}", summary="删除会话")
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]

    try:
        await poe.client.delete_bot(url_botname=bot_id)
        await User.del_user_botId(user, bot_id)
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.delete("/{bot_id}/clear", summary="删除聊天记录（重置会话）")
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    _: dict = Depends(verify_token),
):
    try:
        await poe.client.delete_chat_by_chat_code(chat_code=bot_id)
        # await poe.client.send_chat_break(url_botname=bot_id, chat_code="chat_code")
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


# @router.get("/{bot_id}/history", summary="拉取所有聊天记录")
# async def _(
#     bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
#     _: dict = Depends(verify_token),
# ):
#     try:
#         messages = await poe.client.get_message_history(
#             url_botname=bot_id, get_all=True
#         )
#         return JSONResponse({"code": 2000, "data": messages}, 200)

#     except Exception as e:
#         return handle_exception(str(e))


@router.get("/{bot_id}/info", summary="获取会话基础信息")
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    _: dict = Depends(verify_token),
):
    try:
        data = await poe.client.get_botdata(url_botname=bot_id)
        return JSONResponse(data, 200)

    except Exception as e:
        return handle_exception(str(e))


@router.patch("/{bot_id}", summary="修改bot信息")
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    body: ModifyBotBody = Body(
        example={"model": "ChatGPT", "prompt": "your are dick", "alias": "小芳"}
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]

    model_dict = {
        "ChatGPT": "chinchilla",
        "Claude": "a2",
        "ChatGPT4": "beaver",
        "Claude-2-100k": "a2_2",
    }

    if body.model and body.model not in model_dict:
        return JSONResponse(
            {
                "code": 2000,
                "msg": "Available model: ChatGPT, Claude, ChatGPT4, Claude-2-100k.",
            },
            402,
        )

    try:
        # 更新会话别名
        await User.add_user_botId(user, bot_id, body.alias)
        # 更新bot设置
        await poe.client.edit_bot(
            url_botname=bot_id,
            base_model=model_dict[body.model],
            prompt=body.prompt,
        )
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))
