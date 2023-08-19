from io import BytesIO
from database import *
from models import *
from services import *
from utils import *
from utils.config import *


class BotIdNotFound(Exception):
    def __init__(self):
        pass


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    if "The bot doesn't exist or isn't accessible" in err_msg:
        return JSONResponse({"code": 3002, "msg": "该会话已失效，请创建新会话"}, 500)

    logger.error(err_msg)
    return JSONResponse({"code": 3001, "msg": err_msg}, 500)


model_dict = {
    "ChatGPT": "chinchilla",
    "Claude": "a2",
    "ChatGPT4": "beaver",
    "Claude-2-100k": "a2_2",
}


router = APIRouter()


@router.post(
    "/create",
    summary="创建会话",
    responses={
        200: {
            "description": "创建成功",
            "content": {
                "application/json": {
                    "example": {"bot_id": "会话id"},
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
    if body.model not in model_dict:
        return JSONResponse(
            {
                "code": 2002,
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
            poe.client.bot_code_dict
            await User.add_user_botId(user, bot_id, body.alias)
            return JSONResponse({"bot_id": bot_id}, 200)

        except Exception as e:
            return handle_exception(str(e))


@router.post(
    "/{bot_id}/talk",
    summary="对话（提问）",
    responses={
        200: {
            "description": "回复内容",
            "content": {"text/plain": {"example": "你寄吧谁啊"}},
        }
    },
)
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    body: TalkBody = Body(example={"q": "你好啊"}),
    _: dict = Depends(verify_token),
):
    chat_code = None
    try:
        if _ := poe.client.bot_code_dict[bot_id]:
            chat_code = _[0]
    except KeyError:
        raise BotIdNotFound()

    try:

        # async def generate():
        #     async for resp in poe.client.ask_stream(
        #         url_botname=bot_id,
        #         chat_code=chat_code,
        #         question=body.q,
        #         suggest_able=False,
        #     ):
        #         yield BytesIO(resp.encode("utf-8")).read()

        async for message in poe.client.ask_stream(
            url_botname=bot_id,
            chat_code=chat_code,
            question=body.q,
            suggest_able=False,
        ):
            print(message, end="")

        # return StreamingResponse(generate(), media_type="text/plain")
        return {}

    except Exception as e:
        return handle_exception(str(e))


@router.delete(
    "/{bot_id}",
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


@router.delete(
    "/{bot_id}/reset",
    summary="删除bot的对话记忆，重置对话",
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
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    _: dict = Depends(verify_token),
):
    try:
        chat_code = ""
        if _ := poe.client.bot_code_dict[bot_id]:
            chat_code = _[0]
    except KeyError:
        raise BotIdNotFound()

    try:
        await poe.client.send_chat_break(url_botname=bot_id, chat_code=chat_code)
        return Response(status_code=204)

    except Exception as e:
        return handle_exception(str(e))


@router.get(
    "/{bot_id}/info",
    summary="获取会话基础信息",
    responses={
        200: {
            "description": "无相关响应",
            "content": {
                "application/json": {
                    "example": {
                        "model": "ChatGPT",
                        "prompt": "Your honey~",
                        "history": [
                            {
                                "sender": "bot",
                                "msg": "当然！我很乐意为你提供帮助。请告诉我你需要测试的内容，我会尽力回答你的问题或提供所需的指导。",
                                "id": "TWVzc2FnZToyNTgzODQ1MzUz",
                            },
                            {
                                "sender": "user",
                                "msg": "测试一下",
                                "id": "TWVzc2FnZToyNTgzODYwNzc5",
                            },
                            {
                                "sender": "bot",
                                "msg": "当然！我随时准备好进行测试。请告诉我你想要测试的内容，我将尽力为你提供帮助。无论是技术问题、一般知识还是其他方面，我都会尽力回答你的问题。请提供具体的测试内容，我会尽力满足你的需求。",
                                "id": "TWVzc2FnZToyNTgzODYwNzg4",
                            },
                            {
                                "sender": "user",
                                "msg": "测试一下",
                                "id": "TWVzc2FnZToyNTgzODg1MTU0",
                            },
                            {
                                "sender": "bot",
                                "msg": "当你说“测试一下”，我不清楚你具体想要测试什么。请提供更多细节，让我知道你希望测试的领域或问题。这样，我才能更好地理解你的需求并提供适当的帮助。无论是技术问题、学术知识还是其他方面，只要在我的知识范围内，我都会尽力回答你的问题。请告诉我你想要测试的具体内容，我会尽力满足你的需求。",
                                "id": "TWVzc2FnZToyNTgzODg1MTYy",
                            },
                        ],
                    }
                }
            },
        },
    },
)
async def _(
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    _: dict = Depends(verify_token),
):
    try:
        poe.client.bot_code_dict[bot_id]
    except KeyError:
        raise BotIdNotFound()

    try:
        data = await poe.client.get_bot_info(url_botname=bot_id)
        prompt = data["promptPlaintext"]
        data = await poe.client.get_botdata(url_botname=bot_id)
        model = data["bot"]["baseModelDisplayName"]
        history = []
        for _ in data["chats"]["2i6nb85beiu3y9zml7m"]["messagesConnection"]["edges"]:
            sender = "user" if _["node"]["author"] == "human" else "bot"
            msg = _["node"]["text"]
            id = _["node"]["id"]
            history.append({"sender": sender, "msg": msg, "id": id})

        return JSONResponse({"model": model, "prompt": prompt, "history": history}, 200)

    except Exception as e:
        return handle_exception(str(e))


@router.patch(
    "/{bot_id}",
    summary="修改bot信息",
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
    bot_id: str = Path(description="会话id", example="t3JChplM0pgoNuGVEEyC"),
    body: ModifyBotBody = Body(
        example={"model": "ChatGPT", "prompt": "your are dick", "alias": "小芳"}
    ),
    user_data: dict = Depends(verify_token),
):
    try:
        poe.client.bot_code_dict[bot_id]
    except KeyError:
        raise BotIdNotFound()

    user = user_data["user"]

    if body.model and body.model not in model_dict:
        return JSONResponse(
            {
                "code": 2002,
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
