from io import BytesIO
from time import localtime, strftime
from typing import AsyncIterable

from database.bot_db import Bot
from database.chat_db import Chat
from database.user_db import User
from fastapi import APIRouter, Body, Depends, File, Form, Path, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from models.user_models import (
    AnswerAgain,
    AnswerStop,
    ChatTitleBody,
    CreateBotBody,
    EditBotBody,
    EditSourceBody,
    LoginBody,
    UpdatePasswdBody,
)
from services.jwt_auth import create_token, verify_token
from services.poe_client import poe
from services.poe_lib.type import (
    BotMessageAdded,
    BotMessageCreated,
    ChatTitleUpdated,
    TalkError,
)
from ujson import dumps, loads
from utils.tool_util import logger, user_action

router = APIRouter()


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    logger.error(err_msg)
    return JSONResponse({"code": 3001, "msg": err_msg}, 500)


async def reply_pre_check(user: str, chatCode: str, remain_points: int, price: int):
    # 判断账号授权是否过期
    if await User.is_outdate(user):
        date_string = strftime(
            "%Y-%m-%d %H:%M:%S", localtime(await User.get_expire_date(user) / 1000)
        )
        return JSONResponse(
            {"code": 2009, "msg": f"你的账号授权已于{date_string}过期，无法对话"}, 402
        )

    # 判断会话是否存在
    if chatCode != "0" and not await Chat.chat_exist(user, chatCode):
        return JSONResponse({"code": 2001, "msg": "会话不存在"}, 402)

    # 判断积分够不够
    if remain_points < price:
        return JSONResponse(
            {"code": 2010, "msg": f"可用积分不足，当前可用积分: {remain_points}"}, 402
        )


async def ai_reply(
    user: str,
    chatCode: str,
    chatId: int,
    botName: str,
    messageId: int,
    chat_data: dict,
    new_chat: bool,
) -> AsyncIterable:
    """回答环节"""

    def _yield_data(data_type: str, data: str | dict) -> bytes:
        return BytesIO(
            (dumps({"type": data_type, "data": data}) + "\n").encode("utf-8")
        ).read()

    # 新会话数据
    if new_chat:
        yield _yield_data(
            "newChat",
            {
                "chatCode": chatCode,
                "botInfo": chat_data["botInfo"],
            },
        )

    # 用户的问题元数据
    yield _yield_data(
        "humanMessageCreated",
        chat_data["messageNode"],
    )

    async for _data in poe.client.get_answer(chatId, messageId, new_chat):
        # bot的回答元数据
        if isinstance(_data, BotMessageCreated):
            yield _yield_data(
                "botMessageCreated",
                {
                    "messageId": _data.messageId,
                    "creationTime": _data.creationTime,
                    "text": "",
                    "attachments": [],
                    "author": "bot",
                },
            )

        # AI的回答
        if isinstance(_data, BotMessageAdded):
            yield _yield_data(
                "botMessageAdded", {"state": _data.state, "text": _data.text}
            )

        # 标题更新
        if isinstance(_data, ChatTitleUpdated):
            await Chat.update_title(user, chatCode, _data.title)
            yield _yield_data("chatTitleUpdated", {"title": _data.title})

        # 出错
        if isinstance(_data, TalkError):
            yield _yield_data("talkError", {"err_msg": _data.errMsg})
            logger.error(f"用户:{user}  bot:{botName}  code:{chatCode}  {_data.errMsg}")


@router.post(
    "/login",
    summary="登陆接口",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "accessToken": "eyJhbxxxxxxxxxxxxxxxxxxxxxxxx",
                        "tokenType": "Bearer",
                    }
                }
            },
        },
    },
)
async def _(
    body: LoginBody = Body(
        examples=[{"user": "用户名", "passwd": "sha256加密后的密码"}]
    ),
):
    if not await User.auth_user(body.user, body.passwd):
        return JSONResponse({"code": 2000, "msg": "认证失败"}, 401)

    token = create_token(
        {"user": body.user, "passwd": body.passwd, "eopServer": "by_nikiss"}
    )
    return JSONResponse({"accessToken": token, "tokenType": "Bearer"}, 200)


@router.get(
    "/info",
    summary="获取用户自己的信息",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "user": "user_name",
                        "remainPoints": 500,
                        "monthPoints": 1000,
                        "isAdmin": 0,
                        "resetDate": 4070880000000,
                        "expireDate": 4070880000000,
                    }
                }
            },
        },
    },
)
async def _(user_data: dict = Depends(verify_token)):
    user_info = await User.get_info(user_data["user"])

    return JSONResponse(
        {
            "user": user_info.user,
            "remainPoints": user_info.remain_points,
            "monthPoints": user_info.month_points,
            "isAdmin": user_info.admin,
            "resetDate": user_info.reset_date,
            "expireDate": user_info.expire_date,
        },
        200,
    )


@router.post(
    "/updatePasswd",
    summary="修改密码",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "修改成功",
            "content": None,
        },
    },
)
async def _(
    body: UpdatePasswdBody = Body(
        examples=[{"oldPasswd": "加密的旧密码", "newPasswd": "加密的新密码"}]
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    # test不能让用户自己改密码
    if user == "test":
        return Response(status_code=204)

    if not await User.auth_user(user, body.oldPasswd):
        return JSONResponse({"code": 2000, "msg": "认证失败"}, 401)

    await User.update_passwd(user, body.newPasswd)
    user_action.info(f"用户 {user} 更新了密码")
    return Response(status_code=204)


@router.get(
    "/exploreBots/{category}/{endCursor}",
    summary="探索bot",
    responses={
        200: {
            "description": "categoryList是bot分类，只有cursor为0的时候才返回",
            "content": {
                "application/json": {
                    "example": {
                        "categoryList": [
                            {
                                "categoryName": "Official",
                                "translatedCategoryName": "官方",
                            }
                        ],
                        "bots": [
                            {
                                "model": "ChatGPT",
                                "imgUrl": "https://xxx/bot.jpg",
                                "description": "由gpt-3.5-turbo驱动。",
                                "botType": "官方",
                                "monthlyActive": 0,
                            },
                            {
                                "model": "iKun",
                                "imgUrl": "https://xxx/bot.jpg",
                                "description": "练习时长两年半",
                                "botType": "第三方",
                                "monthlyActive": 114514,
                            },
                        ],
                        "pageInfo": {"endCursor": "1017", "hasNextPage": True},
                    },
                }
            },
        },
    },
)
async def _(
    category: str = Path(description="分类", example="Official"),
    endCursor: str = Path(description="翻页指针，初始是0", example="0"),
    user_data: dict = Depends(verify_token),
):
    try:
        data = await poe.client.explore_bot(category, endCursor)
    except Exception as e:
        return handle_exception(repr(e))

    return JSONResponse(data, 200)


@router.get(
    "/searchBots/{keyWord}/{endCursor}",
    summary="搜索bot",
    responses={
        200: {
            "description": "跟探索bot一样用，不过这个没分类",
            "content": {
                "application/json": {
                    "example": {
                        "bots": [
                            {
                                "model": "ChatGPT",
                                "imgUrl": "https://xxx/bot.jpg",
                                "description": "由gpt-3.5-turbo驱动。",
                                "botType": "官方",
                                "monthlyActive": 0,
                            },
                            {
                                "model": "iKun",
                                "imgUrl": "https://xxx/bot.jpg",
                                "description": "XXXXXX",
                                "botType": "第三方",
                                "monthlyActive": 114514,
                            },
                            {
                                "model": "my_bot",
                                "imgUrl": "https://xxx/bot.jpg",
                                "description": "XXXXXX",
                                "botType": "第三方",
                                "monthlyActive": 114514,
                            },
                        ],
                        "pageInfo": {"endCursor": "20", "hasNextPage": True},
                    },
                }
            },
        },
    },
)
async def _(
    keyWord: str = Path(description="关键字", example="GPT"),
    endCursor: str = Path(description="翻页指针，初始是0", example="0"),
    user_data: dict = Depends(verify_token),
):
    try:
        data = await poe.client.search_bot(keyWord, endCursor)
    except Exception as e:
        return handle_exception(repr(e))

    return JSONResponse(data, 200)


@router.get(
    "/bots",
    summary="拉取用户的bot",
    responses={
        200: {
            "description": "bot列表",
            "content": {
                "application/json": {
                    "example": {
                        "bots": [
                            {
                                "name": "ChatGPT",
                                "imgUrl": "https://xxx",
                                "botType": "官方",
                            },
                            {
                                "name": "CatBot",
                                "imgUrl": "https://xxx",
                                "botType": "自定义",
                            },
                        ]
                    }
                }
            },
        },
    },
)
async def _(user_data: dict = Depends(verify_token)):
    _rows = await Bot.get_user_bot(user_data["user"])
    bot_list = [
        {
            "name": row[0],
            "imgUrl": row[1],
            "botType": row[2],
        }
        for row in _rows
    ]
    return JSONResponse({"bots": bot_list}, 200)


@router.post(
    "/bot/{botName}",
    summary="添加bot",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "添加成功",
        },
    },
)
async def _(
    botName: str = Path(description="bot名称", example="ChatGPT"),
    user_data: dict = Depends(verify_token),
):
    try:
        bot_info = await poe.client.get_bot_info(botName)
    except Exception as e:
        return handle_exception(repr(e))

    user = user_data["user"]
    await Bot.add_bot(
        user,
        botName,
        bot_info["imgUrl"],
        bot_info["botType"],
        bot_info["botHandle"],
        bot_info["botId"],
    )
    user_action.info(f"用户 {user} 添加bot {botName}")
    return Response(status_code=204)


@router.get(
    "/basicBots",
    summary="获取自定义bot可使用的基础bot",
    responses={
        200: {
            "description": "",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "botName": "ChatGPT",
                            "imgUrl": "https://xxx",
                            "botId": 3004,
                            "model": "chinchilla",
                            "isImageGen": False,
                        },
                        {
                            "botName": "DALL-E-3",
                            "imgUrl": "https://xxx",
                            "botId": 2828029,
                            "model": "dalle3",
                            "isImageGen": True,
                        },
                    ]
                }
            },
        }
    },
)
async def _(
    user_data: dict = Depends(verify_token),
):
    try:
        bot_list = await poe.client.get_basic_bot_list()
    except Exception as e:
        return handle_exception(repr(e))

    return JSONResponse(bot_list, 200)


@router.post(
    "/uploadSource",
    summary="上传自定义bot引用资源",
    responses={
        200: {
            "description": "msg_info（消息数据）、response（回答数据）、end（回答完毕）、error（出错，msg里的字符串是原因）",
            "content": {
                "application/json": {
                    "example": {
                        "sourceId": 2380421,
                        "sourceTitle": "fileName or title",
                    },
                }
            },
        }
    },
)
async def _(
    sourceType: str = Form(description="text 或 file"),
    title: str = Form(None, description="标题，type为text才需要"),
    content: str = Form(None, description="内容，type为text才需要"),
    file: UploadFile = File(None, description="type为file才需要"),
    user_data: dict = Depends(verify_token),
):
    files = []
    # 文件资源
    if sourceType == "file" and file:
        _data = {"file_upload": {"attachment": "file"}}
        files.append(("file", await file.read(), file.content_type, file.filename))

    # 文本资源
    else:
        _data = {"text_input": {"title": title, "content": content}}

    try:
        source_data = await poe.client.upload_knowledge_source(_data, files)
    except Exception as e:
        return handle_exception(repr(e))

    return source_data


@router.get(
    "/getTextSource/{sourceId}",
    summary="获取bot引用资源内容（仅限文本）",
    responses={
        200: {
            "description": "资源的标题和内容",
            "content": {
                "application/json": {
                    "example": {
                        "title": "标题",
                        "content": "文本内容",
                    },
                }
            },
        }
    },
)
async def _(
    sourceId: int = Path(description="文本资源id", example=2380421),
    user_data: dict = Depends(verify_token),
):
    try:
        source_data = await poe.client.get_text_knowledge_source(sourceId)
    except Exception as e:
        return handle_exception(repr(e))

    return source_data


@router.post(
    "/editTextSource",
    summary="编辑bot引用资源（仅限文本）",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "创建成功",
        },
    },
)
async def _(
    body: EditSourceBody = Body(
        examples=[
            {
                "sourceId": 2380421,
                "title": "标题",
                "content": "内容",
            }
        ]
    ),
    user_data: dict = Depends(verify_token),
):
    try:
        await poe.client.edit_text_knowledge_source(
            body.sourceId, body.title, body.content
        )
    except Exception as e:
        return handle_exception(repr(e))

    return Response(status_code=204)


@router.post(
    "/createBot",
    summary="创建自定义bot",
    description="sourceIds可以空着",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "创建成功",
        },
    },
)
async def _(
    body: CreateBotBody = Body(
        examples=[
            {
                "botName": "CatBot",
                "baseBotId": 3004,
                "baseBotModel": "chinchilla",
                "description": "这是个猫娘",
                "prompt": "You are the CatBot. You will try to respond to the user's questions, but you get easily distracted.",
                "citeSource": True,
                "sourceIds": [2380421, 2380434],
            }
        ],
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]

    # 判断账号授权是否过期
    if await User.is_outdate(user):
        date_string = strftime(
            "%Y-%m-%d %H:%M:%S", localtime(await User.get_expire_date(user) / 1000)
        )
        return JSONResponse(
            {"code": 2009, "msg": f"你的账号授权已于{date_string}过期，无法对话"}, 402
        )

    if await Bot.bot_exist(user, body.botName):
        return JSONResponse({"code": 2001, "msg": "已经有相同名字的bot"}, 402)

    try:
        # 创建bot
        bot_info = await poe.client.create_bot(
            body.baseBotId,
            body.baseBotModel,
            body.description,
            body.prompt,
            body.citeSource,
            body.sourceIds,
        )
    except Exception as e:
        return handle_exception(repr(e))

    await Bot.add_bot(
        user,
        body.botName,
        bot_info["imgUrl"],
        bot_info["botType"],
        bot_info["botHandle"],
        bot_info["botId"],
    )
    user_action.info(
        f"用户 {user} 添加自定义bot {body.botName}（{bot_info['botHandle']}）"
    )

    return Response(status_code=204)


@router.get(
    "/editBot/{botName}",
    summary="获取待编辑bot信息",
    responses={
        200: {
            "description": "",
            "content": {
                "application/json": {
                    "example": {
                        "basicBotList": "（数据参考接口basicBotList）",
                        "botInfo": {
                            "botName": "CatBot",
                            "botId": 4368380,
                            "botHandle": "1Fp4BqjkQKpmiSj5Taey",
                            "baseBotId": 3004,
                            "baseBotModel": "chinchilla",
                            "description": "这是机器人的简介",
                            "prompt": "这是机器人的prompt内容",
                            "citeSource": True,
                            "sourceList": [
                                {
                                    "sourceId": 2413096,
                                    "sourceType": "text",
                                    "title": "tttttttt",
                                    "lastUpdatedTime": 1717739865091089,
                                },
                                {
                                    "sourceId": 2413098,
                                    "sourceType": "file",
                                    "title": "startserver.sh",
                                    "lastUpdatedTime": 1717739829755288,
                                },
                            ],
                        },
                    }
                }
            },
        }
    },
)
async def _(
    botName: str = Path(description="bot名称", example="CatBot"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)

    try:
        edit_bot_info = await poe.client.get_edit_bot_info(bot_handle)
    except Exception as e:
        return handle_exception(repr(e))
    # todo bot_info未筛选
    return JSONResponse(edit_bot_info, 200)


@router.post(
    "/editBot/{botName}",
    summary="修改自定义bot信息",
    description="addSourceIds 和 removeSourceIds 如果不变就空着",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "修改成功",
        },
    },
)
async def _(
    botName: str = Path(description="bot名称", example="CatBot"),
    body: EditBotBody = Body(
        examples=[
            {
                "botName": "CatBot",
                "botId": 4368380,
                "botHandle": "1Fp4BqjkQKpmiSj5Taey",
                "baseBotId": 3004,
                "baseBotModel": "chinchilla",
                "description": "这是个猫娘",
                "prompt": "You are the CatBot. You will try to respond to the user's questions, but you get easily distracted.",
                "citeSource": True,
                "addSourceIds": [2380421, 2380434],
                "removeSourceIds": [2380421, 2380434],
            }
        ],
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    # todo 自定义bot不能重名

    bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)
    if bot_type != "自定义":
        return JSONResponse({"code": 2001, "msg": "只能修改自定义bot"}, 402)

    if botName != body.botName and await Bot.bot_exist(user, body.botName):
        return JSONResponse({"code": 2001, "msg": "已经有相同名字的bot"}, 402)

    try:
        # 获取bot信息
        await poe.client.edit_bot(
            body.botId,
            body.botHandle,
            body.baseBotId,
            body.baseBotModel,
            body.description,
            body.prompt,
            body.citeSource,
            body.addSourceIds,
            body.removeSourceIds,
        )
    except Exception as e:
        return handle_exception(repr(e))

    await Bot.update_botName(user, body.botId, body.botName)

    return Response(status_code=204)


@router.delete(
    "/bot/{botName}",
    summary="删除bot",
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
    botName: str = Path(description="bot名称", example="ChatGPT"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    # 先删除这个bot下的会话
    _rows = await Chat.get_user_chat(user, botName)
    for row in _rows:
        try:
            await poe.client.delete_chat(row[0], row[6])
            await Chat.delete_chat(user, row[0])
        except Exception as e:
            return handle_exception(repr(e))

    # 判断是否为自定义bot，如果是需要替换handle，handle为真实名称，并删除
    try:
        bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)
        if bot_type == "自定义":
            await poe.client.delete_bot(bot_handle, bot_id)
    except Exception as e:
        return handle_exception(repr(e))

    await Bot.remove_bot(user, botName)

    if bot_type == "自定义":
        botName += f"（{bot_handle}）"

    user_action.info(f"用户 {user} 删除bot {botName}")
    return Response(status_code=204)


@router.get(
    "/bot/{botName}",
    summary="查看bot信息",
    responses={
        200: {
            "description": """
allowImage和allowFile 指是否支持图片或文件上传<br>
uploadFileSizeLimit 指文件上传大小限制，50000000就是50MB<br>
price 是每次对话需要的积分<br>
remainTalkTimes 是剩余积分可与这个bot的对话次数<br>
added 指是否已经添加到我的bot里""",
            "content": {
                "application/json": {
                    "example": {
                        "botName": "ChatGPT",
                        "botId": 3004,
                        "botHandle": "chinchilla",
                        "description": "这个是GPT3.5",
                        "allowImage": True,
                        "allowFile": True,
                        "uploadFileSizeLimit": 50000000,
                        "imgUrl": "https://xxx",
                        "price": 20,
                        "remainTalkTimes": 66,
                        "botType": "官方/第三方/自定义",
                        "added": True,
                        "canAccess": True,
                    }
                }
            },
        },
    },
)
async def _(
    botName: str = Path(description="bot名称", example="ChatGPT"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    added = await Bot.bot_exist(user, botName)

    # 判断是否为自定义bot，如果是需要替换handle，handle为真实名称
    custom_bot_displayname = ""
    if added:
        bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)
        if bot_type == "自定义":
            custom_bot_displayname = botName
            botName = bot_handle
    try:
        bot_info = await poe.client.get_bot_info(botName)
    except Exception as e:
        return handle_exception(repr(e))

    # 如果为自定义bot，返回要改回去用户设置的botName
    if custom_bot_displayname:
        bot_info["botName"] = custom_bot_displayname

    bot_info["added"] = added

    # 计算可对话次数
    remain_points = await User.get_remain_points(user)
    bot_info["remainTalkTimes"] = int(remain_points / bot_info["price"])

    return JSONResponse(bot_info, 200)


@router.get(
    "/chats/{botName}",
    summary="拉取会话",
    responses={
        200: {
            "description": "会话列表",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "chatCode": "abc23kjkwei",
                            "title": "会话1",
                            "bot": "ChatGPT",
                            "imgUrl": "https://xxx",
                            "lastTalkTime": 1719676800000,
                            "disable": 0,
                        },
                        {
                            "chatCode": "werwea123sda",
                            "title": "会话2",
                            "bot": "ChatGPT",
                            "imgUrl": "https://xxx",
                            "lastTalkTime": 1719676800000,
                            "disable": 0,
                        },
                    ]
                }
            },
        },
    },
)
async def _(
    botName: str = Path(description="bot名称，如果写all则拉取所有", example="all"),
    user_data: dict = Depends(verify_token),
):
    if botName == "all":
        botName = ""
    _rows = await Chat.get_user_chat(user_data["user"], botName)
    chat_list = [
        {
            "chatCode": row[0],
            "title": row[1],
            "bot": row[2],
            "imgUrl": row[3],
            "lastTalkTime": row[4],
            "disable": row[5],
        }
        for row in _rows
    ]
    return JSONResponse(chat_list, 200)


@router.get(
    "/chat/{chatCode}/{cursor}",
    summary="查看会话详细信息（包含聊天记录）",
    responses={
        200: {
            "description": """
botInfo跟bot详细信息一样，只有cursor为0才返回<br>
attachments 是附件，如文件<br>
chat_break 指使用了清空上下文""",
            "content": {
                "application/json": {
                    "example": {
                        "botInfo": {
                            "botName": "ChatGPT",
                            "botId": 3004,
                            "botHandle": "chinchilla",
                            "description": "这个是GPT3.5",
                            "allowImage": True,
                            "allowFile": True,
                            "uploadFileSizeLimit": 50000000,
                            "imgUrl": "https://xxx",
                            "price": 20,
                            "botType": "官方",
                            "canAccess": True,
                        },
                        "historyNodes": [
                            {
                                "messageId": 2692997857,
                                "creationTime": 1692964266475260,
                                "text": "总结这份文件",
                                "attachments": [],
                                "author": "human",
                            },
                            {
                                "messageId": 2692997880,
                                "creationTime": 1692964266638975,
                                "text": "好的，内容XXX",
                                "attachments": [],
                                "author": "bot",
                            },
                            {
                                "messageId": 2692997880,
                                "creationTime": 1692964266638975,
                                "text": "",
                                "attachments": [],
                                "author": "chat_break",
                            },
                        ],
                        "pageInfo": {
                            "hasPreviousPage": True,
                            "startCursor": "2692997857",
                        },
                    }
                }
            },
        },
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    cursor: str = Path(description="翻页指针，初始是0", example="0"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    try:
        botName, chatId, title = await Chat.get_chat_info(user, chatCode)
        chat_info = await poe.client.get_chat_info(chatCode, chatId, cursor)
    except Exception as e:
        return handle_exception(repr(e))

    # 判断是否为自定义bot，如果是需要替换handle为用户设置的名称
    bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)
    if bot_type == "自定义":
        chat_info["botInfo"]["botName"] = botName

    return JSONResponse(chat_info, 200)


@router.post(
    "/titleUpdate/{chatCode}",
    summary="修改会话标题",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "修改成功",
        },
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    body: ChatTitleBody = Body(
        examples=[
            {
                "title": "新名称",
            }
        ]
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    await Chat.update_title(user, chatCode, body.title)
    return Response(status_code=204)


@router.post(
    "/talk/{chatCode}",
    summary="发送问题，并获取回答",
    responses={
        200: {
            "description": """
消息类型type有5种<br/>
1. newChat （新建会话，需要跳转到对话页面）<br/>
    data例子 {"chatCode": XXXYYY, "botInfo": [巴拉巴拉]} botInfo参考接口《查看bot信息》的响应 <br/>
2. humanMessageCreated （问题id、时间）<br/>
    data例子 {"messageId": 205457903902, "creationTime": 17192415022112113, "text": "", "attachments": [], "author": "human"} <br/>
3. botMessageCreated （回答id、时间）<br/>
    data例子 {"messageId": 205457903903, "creationTime": 1719241503367779, "text": "", "attachments": [], "author": "bot"} <br/>
4. botMessageAdded （回答内容）<br/>
    data例子 {"state": "incomplete/complete/cancelled", "text": "回答的内容"} <br/>
5. chatTitleUpdated （会话标题，只有新会话才有）<br/>
    data例子 {"title": "标题"} <br/>
7. talkError （回答出错）<br/>
    data例子 {"err_msg": "错误原因"} """,
            "content": {
                "application/json": {
                    "example": {
                        "type": "消息类型",
                        "data": "回答内容",
                    },
                }
            },
        }
    },
)
async def _(
    chatCode: str = Path(description="chat code，如果为0则新建会话", example="0"),
    botName: str = Form(description="bot名称"),
    question: str = Form(None, description="问题内容，可以只发文件不发文本"),
    price: int = Form(description="所需积分"),
    files: list[UploadFile] = File(None, description="要上传的附件，不需要就不发"),
    user_data: dict = Depends(verify_token),
):
    if not question:
        question = ""
    user = user_data["user"]
    remain_points = await User.get_remain_points(user)
    # 预检查
    if json_response := await reply_pre_check(user, chatCode, remain_points, price):
        return json_response
    # 新会话判断是否添加了bot，如果没添加就加上
    if chatCode == "0" and not await Bot.bot_exist(user, botName):
        try:
            bot_info = await poe.client.get_bot_info(botName)
        except Exception as e:
            return handle_exception(repr(e))
        await Bot.add_bot(
            user,
            botName,
            bot_info["imgUrl"],
            bot_info["botType"],
            bot_info["botHandle"],
            bot_info["botId"],
        )
        user_action.info(f"用户 {user} 添加bot {botName}")
    #################
    ### 提问环节
    #################
    chatId = 0
    if chatCode != "0":
        botName, chatId, title = await Chat.get_chat_info(user, chatCode)
    bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)
    # 处理附件
    file_list: list[tuple] = []
    if files:
        for index, file in enumerate(files):
            file_list.append(
                (
                    f"file{index}",
                    await file.read(),
                    file.content_type,
                    file.filename,
                )
            )
    # 发起问题请求
    try:
        chat_data = await poe.client.send_question(
            bot_handle, chatId, question, price, file_list
        )
    except Exception as e:
        return handle_exception(repr(e))

    new_chat = False
    if chatCode == "0":
        # 保存新会话记录
        user_action.info(
            f"用户 {user} 新会话 {botName} chatCode {chat_data['chatCode']}"
        )
        await Chat.new_chat(
            chat_data["chatCode"],
            chat_data["chatId"],
            user,
            "新建聊天",
            botName,
            chat_data["botInfo"]["imgUrl"],
        )
        chatCode = chat_data["chatCode"]
        chatId = chat_data["chatId"]
        new_chat = True
        # 把bot类型补上
        chat_data["botType"] = bot_type
    # 获取消息id
    messageId = chat_data["messageNode"]["messageId"]
    # 减去用户积分
    await User.update_remain_points(user, remain_points - price)
    # 更新最后对话时间
    await Chat.update_last_talk_time(user, chatCode)
    user_action.info(f"用户 {user} 对话 {botName} chatCode {chatCode} 积分 {price}")

    #################
    ### 回答环节
    #################
    return StreamingResponse(
        ai_reply(user, chatCode, chatId, botName, messageId, chat_data, new_chat),
        media_type="text/event-stream",
        status_code=200,
    )


@router.post(
    "/talkAgain/{chatCode}",
    summary="重新回答，请求成功后需要重新拉取回答",
    description="messageId是要重新回答的id，price是这个bot的所需积分",
    responses={
        200: {
            "description": "跟发送问题的响应一样",
            "content": {
                "application/json": {
                    "example": {
                        "type": "消息类型",
                        "data": "回答内容",
                    },
                }
            },
        }
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    body: AnswerAgain = Body(
        examples=[
            {
                "messageId": 12312312,
                "price": 20,
            }
        ],
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    messageId = body.messageId
    price = body.price
    remain_points = await User.get_remain_points(user)
    # 预检查
    if json_response := await reply_pre_check(user, chatCode, remain_points, price):
        return json_response
    # 发起重新回答的请求
    try:
        await poe.client.answer_again(chatCode, messageId, price)
    except Exception as e:
        return handle_exception(repr(e))

    botName, chatId, title = await Chat.get_chat_info(user, chatCode)

    # 减去用户积分
    await User.update_remain_points(user, remain_points - price)
    # 更新最后对话时间
    await Chat.update_last_talk_time(user, chatCode)
    user_action.info(f"用户 {user} 对话 {botName} chatCode {chatCode} 积分 {price}")

    #################
    ### 回答环节
    #################
    return StreamingResponse(
        ai_reply(user, chatCode, chatId, botName, messageId, {}, False),
        media_type="text/event-stream",
        status_code=200,
    )


@router.post(
    "/answerStop/{chatCode}",
    summary="停止回答",
    description="写要停止回答的messageId",
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
    chatCode: str = Path(description="chatCode", example="XXXYYY"),
    body: AnswerStop = Body(
        examples=[
            {
                "messageId": 12312312,
            }
        ],
    ),
    user_data: dict = Depends(verify_token),
):
    try:
        await poe.client.talk_stop(chatCode, body.messageId)
    except Exception as e:
        return handle_exception(repr(e))

    return Response(status_code=204)


@router.delete(
    "/chatMemory/{chatCode}",
    summary="清除上下文记忆",
    responses={
        200: {
            "description": "响应的数据是chat_break的数据",
            "content": {
                "application/json": {
                    "example": {
                        "messageId": 2692997880,
                        "creationTime": 1692964266638975,
                        "text": "",
                        "attachments": [],
                        "author": "chat_break",
                    },
                }
            },
        }
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    botName, chatId, title = await Chat.get_chat_info(user, chatCode)

    try:
        data = await poe.client.send_chat_break(chatCode, chatId)
    except Exception as e:
        return handle_exception(repr(e))

    return JSONResponse(data, 200)


@router.delete(
    "/chat/{chatCode}",
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
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    botName, chatId, title = await Chat.get_chat_info(user, chatCode)
    try:
        await poe.client.delete_chat(chatCode, chatId)
    except Exception as e:
        return handle_exception(repr(e))

    await Chat.delete_chat(user, chatCode)
    user_action.info(f"用户 {user} 删除会话 bot{botName} 会话{chatCode}")
    return Response(status_code=204)
