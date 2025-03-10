from io import BytesIO
from time import localtime, strftime
from typing import AsyncIterable

import models.user_req_models as req_models
import models.user_resp_models as resp_models
from database.bot_db import Bot
from database.chat_db import Chat
from database.config_db import Config
from database.user_db import User
from fastapi import APIRouter, Body, Depends, File, Form, Path, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from services.jwt_auth import create_token, verify_token
from services.poe_client import poe
from services.poe_lib.type import (
    BotMessageAdd,
    ChatTitleUpdated,
    FileTooLarge,
    NeedDeleteChat,
    PriceCost,
    TalkError,
    UnsupportedFileType,
)
from ujson import dump, dumps
from utils.gtranslate.client import Translator
from utils.tool_util import logger, user_action

router = APIRouter()


def response_500(err_msg: str) -> JSONResponse:
    """500响应"""
    logger.error(err_msg)
    return JSONResponse({"code": 3001, "msg": err_msg, "data": None}, 500)


def response_400(code: int, msg: str, status_code: int = 402) -> Response:
    """400响应"""
    return JSONResponse(
        {"code": code, "msg": msg, "data": None},
        status_code,
    )


def response_200(data=None, msg="success") -> Response:
    """200响应"""
    return JSONResponse(
        {"code": 0, "msg": msg, "data": data},
        200,
    )


async def reply_pre_check(user: str, chatCode: str, remain_points: int, price: int):
    # 判断账号授权是否过期
    if await User.is_outdate(user):
        date_string = strftime(
            "%Y-%m-%d %H:%M:%S", localtime(await User.get_expire_date(user) / 1000)
        )
        return response_400(2009, f"你的账号授权已于{date_string}过期，无法对话")

    # 判断会话是否存在
    if chatCode != "0" and not await Chat.chat_exist(user, chatCode):
        return response_400(2001, "会话不存在")

    # 判断积分够不够
    if remain_points < price:
        return response_400(2010, f"可用积分不足，当前可用积分: {remain_points}")


async def ai_reply(
    user: str,
    chatCode: str,
    chat_id: int,
    botName: str,
    botHandle: str,
    messageId: int,
    chat_data: dict,
    new_chat: bool,
    remain_points: int,
) -> AsyncIterable:
    """回答环节"""

    def _yield_data(data_type: str, data: str | dict) -> bytes:
        return BytesIO(
            (
                dumps(
                    {
                        "code": 0,
                        "msg": "success",
                        "data": {"dataType": data_type, "dataContent": data},
                    }
                )
                + "\n"
            ).encode("utf-8")
        ).read()

    # 新会话数据
    if new_chat:
        yield _yield_data(
            "newChat",
            {"chatCode": chatCode, "botInfo": chat_data["botInfo"]},
        )

    # 用户的问题元数据
    yield _yield_data("humanMessageAdd", chat_data["messageNode"])

    async for _data in poe.client.get_answer(chat_id, messageId, new_chat):
        # AI的回答
        if isinstance(_data, BotMessageAdd):
            yield _yield_data(
                "botMessageAdd",
                {
                    "state": _data.state,
                    "messageId": _data.messageId,
                    "creationTime": _data.creationTime,
                    "text": _data.text,
                    "attachments": [
                        attachment.model_dump() for attachment in _data.attachments
                    ],
                    "author": "bot",
                },
            )

            if _data.state != "incomplete":
                await Chat.update_last_content(user, chatCode, _data.text)
            if _data.state not in ["complete", "incomplete", "cancelled"]:
                yield _yield_data("talkError", {"errMsg": _data.messageStateText})

        # 标题更新
        if isinstance(_data, ChatTitleUpdated):
            await Chat.update_title(user, chatCode, _data.title)
            yield _yield_data("chatTitleUpdated", {"title": _data.title})

        # 花费更新
        if isinstance(_data, PriceCost):
            # 减去用户积分
            await User.update_remain_points(user, remain_points - _data.price)
            user_action.info(
                f"用户 {user} 对话 {botName} ({botHandle}) chatCode {chatCode} 积分 {_data.price}"
            )

        # 出错
        if isinstance(_data, TalkError):
            yield _yield_data("talkError", {"errMsg": _data.errMsg})
            logger.error(
                f"用户:{user}  {botName} ({botHandle})   chatCode:{chatCode}  {_data.errMsg}"
            )
            user_action.info(
                f"出错 用户:{user}  {botName} ({botHandle})   chatCode:{chatCode}  {_data.errMsg}"
            )


@router.post(
    "/login",
    summary="登陆接口",
    responses={200: {"model": resp_models.BasicRespBody[resp_models.LoginRespBody]}},
)
async def _(
    body: req_models.LoginReqBody = Body(
        examples=[{"user": "用户名", "passwd": "sha256加密后的密码"}]
    ),
):
    if not await User.auth_user(body.user, body.passwd):
        return JSONResponse({"code": 2000, "msg": "认证失败"}, 401)

    token = create_token(
        {"user": body.user, "passwd": body.passwd, "eopServer": "by_nikiss"}
    )

    return response_200(
        {
            "accessToken": token,
            "tokenType": "Bearer",
        },
    )


@router.get(
    "/info",
    summary="获取用户自己的信息",
    responses={200: {"model": resp_models.BasicRespBody[resp_models.UserInfoRespBody]}},
)
async def _(user_data: dict = Depends(verify_token)):
    user_info = await User.get_info(user_data["user"])

    return response_200(
        {
            "user": user_info.user,
            "remainPoints": user_info.remain_points,
            "monthPoints": user_info.month_points,
            "isAdmin": True if user_info.admin else False,
            "resetDate": user_info.reset_date,
            "expireDate": user_info.expire_date,
        },
    )


@router.post(
    "/updatePasswd",
    summary="修改密码",
    responses={
        200: {"description": "修改成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    body: req_models.UpdatePasswdReqBody = Body(
        examples=[{"oldPasswd": "加密的旧密码", "newPasswd": "加密的新密码"}]
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    # test不能让用户自己改密码
    if user == "test":
        return response_200()

    if not await User.auth_user(user, body.oldPasswd):
        return JSONResponse({"code": 2000, "msg": "认证失败"}, 401)

    await User.update_passwd(user, body.newPasswd)
    user_action.info(f"用户 {user} 更新了密码")

    return response_200()


@router.get(
    "/exploreBots/{category}/{endCursor}",
    summary="探索bot",
    responses={
        200: {
            "description": "categoryList是bot分类，只有cursor为0的时候才返回",
            "model": resp_models.BasicRespBody[resp_models.ExploreBotsRespBody],
        }
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
        return response_500(repr(e))

    return response_200(data)


@router.get(
    "/searchBots/{keyWord}/{endCursor}",
    summary="搜索bot",
    responses={
        200: {"model": resp_models.BasicRespBody[resp_models.SearchBotsRespBody]}
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
        return response_500(repr(e))

    return response_200(data)


@router.get(
    "/bots",
    summary="拉取用户的bot",
    responses={
        200: {
            "description": "bot列表",
            "model": resp_models.BasicRespBody[list[resp_models.UserBotRespBody]],
        }
    },
)
async def _(user_data: dict = Depends(verify_token)):
    _rows = await Bot.get_user_bot(user_data["user"])
    bot_list = [
        {
            "botName": row[0],
            "imgUrl": row[1],
            "botType": row[2],
            "botHandle": row[4],
        }
        for row in _rows
    ]

    return response_200(bot_list)


@router.post(
    "/bot/{botName}",
    summary="添加bot",
    responses={
        200: {"description": "添加成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    botName: str = Path(description="bot名称", example="ChatGPT"),
    user_data: dict = Depends(verify_token),
):
    try:
        bot_info = await poe.client.get_bot_info(botName)
    except Exception as e:
        return response_500(repr(e))

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

    return response_200()


@router.get(
    "/basicBots",
    summary="获取自定义bot可使用的基础bot",
    responses={
        200: {
            "description": "基础bot列表",
            "model": resp_models.BasicRespBody[resp_models.BasicBotRespBody],
        }
    },
)
async def _(
    user_data: dict = Depends(verify_token),
):
    try:
        basic_bot_data = await poe.client.get_basic_bot_data()
    except Exception as e:
        return response_500(repr(e))

    return response_200(basic_bot_data)


@router.post(
    "/uploadSource",
    summary="上传自定义bot引用的资源",
    responses={
        200: {"model": resp_models.BasicRespBody[resp_models.UploadSourceRespBody]}
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

    except UnsupportedFileType:
        return response_400(2003, "文件类型不支持")

    except FileTooLarge:
        return response_400(2004, "文件过大")

    except Exception as e:
        return response_500(repr(e))

    return response_200(source_data)


@router.get(
    "/getTextSource/{sourceId}",
    summary="获取bot引用资源内容用于修改（仅限文本）",
    responses={
        200: {"model": resp_models.BasicRespBody[resp_models.GetTextSourceRespBody]}
    },
)
async def _(
    sourceId: int = Path(description="文本资源id", example=2380421),
    user_data: dict = Depends(verify_token),
):
    try:
        source_data = await poe.client.get_text_knowledge_source(sourceId)
    except Exception as e:
        return response_500(repr(e))

    return response_200(source_data)


@router.post(
    "/editTextSource",
    summary="编辑bot引用资源（仅限文本）",
    responses={
        200: {"description": "修改成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    body: req_models.EditSourceReqBody = Body(
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
    except UnsupportedFileType:
        return response_400(2003, "文件类型不支持")

    except FileTooLarge:
        return response_400(2004, "文件过大")

    except Exception as e:
        return response_500(repr(e))

    return response_200()


@router.post(
    "/createBot",
    summary="创建自定义bot",
    description="sourceIds可以空着",
    responses={
        200: {
            "description": "创建成功",
            "model": resp_models.BasicRespBody[resp_models.CreateBotBody],
        },
    },
)
async def _(
    body: req_models.CreateBotReqBody = Body(
        examples=[
            {
                "botName": "CatBot",
                "baseBotId": 3004,
                "baseBotModel": "chinchilla",
                "description": "这是个猫娘",
                "prompt": "You are the CatBot. You will try to respond to the user's questions, but you get easily distracted.",
                "citeSource": False,
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
        return response_400(2009, f"你的账号授权已于{date_string}过期，无法对话")

    if await Bot.custom_bot_exist(user, body.botName):
        return response_400(2001, "已经有相同名字的自定义bot")

    try:
        # 创建bot
        bot_info = await poe.client.create_bot(
            body.baseBotId,
            body.baseBotModel,
            body.description
            if body.description
            else f"由用户{user}创建的{body.botName}",
            body.prompt,
            body.citeSource,
            body.sourceIds,
        )
    except Exception as e:
        return response_500(repr(e))

    await Bot.add_bot(
        user,
        body.botName,
        bot_info["imgUrl"],
        bot_info["botType"],
        bot_info["botHandle"],
        bot_info["botId"],
    )
    user_action.info(
        f"用户 {user} 添加自定义bot {body.botName} {bot_info['botHandle']}"
    )

    return response_200({"botHandle": bot_info["botHandle"]})


@router.get(
    "/editBot/{botHandle}",
    summary="获取待编辑bot信息",
    responses={
        200: {"model": resp_models.BasicRespBody[resp_models.GetEditBotRespBody]}
    },
)
async def _(
    botHandle: str = Path(description="bot Handle", example="1Fp4BqjkQKpmiSj5Taey"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]

    try:
        bot_type, bot_name, bot_id = await Bot.get_bot_info(user, botHandle)
        # 自定义bot的时候是用bot Handle
        edit_bot_info = await poe.client.get_edit_bot_info(bot_name, botHandle)
    except Exception as e:
        return response_500(repr(e))

    return response_200(edit_bot_info)


@router.post(
    "/editBot",
    summary="修改自定义bot信息",
    description="addSourceIds 和 removeSourceIds 如果不变就空着",
    responses={
        200: {"description": "修改成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    body: req_models.EditBotReqBody = Body(
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

    bot_type, bot_name, bot_id = await Bot.get_bot_info(user, body.botHandle)
    if bot_type != "自定义":
        return response_400(2001, "只能修改自定义bot")

    if bot_name != body.botName and await Bot.custom_bot_exist(user, body.botName):
        return response_400(2001, "已经有相同名字的自定义bot")

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
        return response_500(repr(e))

    await Bot.update_bot_name(user, body.botHandle, body.botName)

    return response_200()


@router.delete(
    "/bot/{botHandle}",
    summary="删除bot",
    responses={
        200: {"description": "删除成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    botHandle: str = Path(description="bot Handle", example="1Fp4BqjkQKpmiSj5Taey"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]

    try:
        bot_type, bot_name, bot_id = await Bot.get_bot_info(user, botHandle)
        if bot_type == "自定义":
            await poe.client.delete_bot(botHandle, bot_id)

        if bot_type == "第三方":
            await poe.client.remove_bot(bot_name, bot_id)

    except Exception as e:
        return response_500(repr(e))

    await Bot.remove_bot(user, botHandle)

    user_action.info(f"用户 {user} 删除bot {bot_name} {botHandle}")

    return response_200()


@router.get(
    "/bot/{botName}",
    summary="查看bot信息（如果是自定义bot需要把botName改为botHandle）",
    responses={200: {"model": resp_models.BasicRespBody[resp_models.BotInfo]}},
)
async def _(
    botName: str = Path(description="bot名称", example="ChatGPT"),
    user_data: dict = Depends(verify_token),
):
    try:
        bot_info = await poe.client.get_bot_info(botName)
    except Exception as e:
        return response_500(repr(e))

    user = user_data["user"]
    added = await Bot.bot_exist(user, bot_info["botHandle"])
    bot_info["added"] = added
    # 判断是否为自定义bot，如果是需要替换名称为自定义名称
    if added:
        # 如果是自定义bot，botName等于botHandle
        bot_type, bot_name, bot_id = await Bot.get_bot_info(user, bot_info["botHandle"])
        # 如果是自定义bot，botName要改为自定义的
        if bot_type == "自定义":
            bot_info["botName"] = bot_name
        # 如果已经添加就使用数据库的类型，否则可能private会判断错误
        bot_info["botType"] = bot_type

    return response_200(bot_info)


@router.get(
    "/chats/{botHandle}",
    summary="拉取会话",
    responses={
        200: {
            "description": "会话列表",
            "model": resp_models.BasicRespBody[list[resp_models.ChatRespBody]],
        },
    },
)
async def _(
    botHandle: str = Path(description="bot Handle，如果写all则拉取所有", example="all"),
    user_data: dict = Depends(verify_token),
):
    if botHandle == "all":
        botHandle = ""
    _rows = await Chat.get_user_chat(user_data["user"], botHandle)
    chat_list = [
        {
            "chatCode": row[0],
            "title": row[1],
            "botName": row[2],
            "botHandle": row[3],
            "imgUrl": row[4],
            "lastTalkTime": row[5],
            "lastContent": row[6],
        }
        for row in _rows
    ]
    return response_200(chat_list)


@router.get(
    "/chat/{chatCode}/{cursor}",
    summary="查看会话详细信息（包含聊天记录）",
    responses={
        200: {
            "description": """
botInfo只有cursor为0才返回<br>
attachments 是附件<br>
chat_break 指使用了清空上下文""",
            "model": resp_models.BasicRespBody[resp_models.ChatInfoRespBody],
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
        bot_name, bot_handle, chat_id, title = await Chat.get_chat_info(user, chatCode)
        chat_info = await poe.client.get_chat_info(chatCode, chat_id, cursor)
    except Exception as e:
        return response_500(repr(e))

    # 判断是否为自定义bot，如果是需要替换handle为用户设置的名称
    if cursor == "0" and await Bot.bot_exist(user, bot_handle):
        bot_type, bot_name, bot_id = await Bot.get_bot_info(user, bot_handle)
        if bot_type == "自定义":
            chat_info["botInfo"]["botName"] = bot_name
            chat_info["botInfo"]["added"] = True
            chat_info["botInfo"]["botType"] = bot_type

    with open("tmp.json", "w", encoding="utf-8") as w:
        dump(chat_info, w, ensure_ascii=False)

    return response_200(chat_info)


@router.post(
    "/titleUpdate/{chatCode}",
    summary="修改会话标题",
    responses={
        200: {"description": "修改成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    body: req_models.ChatTitleReqBody = Body(
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

    return response_200()


@router.post(
    "/talk/{chatCode}",
    summary="发送问题，并获取回答",
    responses={
        200: {
            "description": """
消息类型type有5种<br/>
newChat -- 新建会话，需要跳转到对话页面 <br/>
<br/>
humanMessageAdd -- 问题内容 <br/>
<br/>
botMessageAdd -- 回答内容 <br/>
<br/>
chatTitleUpdated -- 会话标题，只有新会话才有 <br/>
<br/>
talkError -- 回答出错 <br/>
""",
            "model": resp_models.BasicRespBody[resp_models.TalkRespBody],
        }
    },
)
async def _(
    chatCode: str = Path(description="chat code，如果为0则新建会话", example="0"),
    botName: str = Form(description="bot name"),
    botHandle: str = Form(description="bot handle"),
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
    #################
    ### 新会话判断是否添加了bot，如果没添加就加上（自定义bot一定已添加）
    #################
    if not await Bot.bot_exist(user, botHandle):
        try:
            bot_info = await poe.client.get_bot_info(botName)
        except Exception as e:
            return response_500(repr(e))
        await Bot.add_bot(
            user,
            botName,
            bot_info["imgUrl"],
            bot_info["botType"],
            bot_info["botHandle"],
            bot_info["botId"],
        )
    #################
    ### 提问环节
    #################
    chat_id = 0
    if chatCode != "0":
        bot_name, bot_handle, chat_id, title = await Chat.get_chat_info(user, chatCode)
    # 检查是否为用户的bot，顺便拿bot type
    bot_type, bot_name, bot_id = await Bot.get_bot_info(user, botHandle)
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
        async with poe.client.send_question_lock:
            chat_data = await poe.client.send_question(
                botHandle, chat_id, question, file_list
            )
    except UnsupportedFileType:
        return response_400(2003, "文件类型不支持")

    except FileTooLarge:
        return response_400(2004, "文件过大")

    except NeedDeleteChat:
        await Chat.delete_chat(user, chatCode)
        return response_400(2005, "会话已被删除")

    except Exception as e:
        return response_500(repr(e))

    new_chat = False
    if chatCode == "0":
        # 保存新会话记录
        await Chat.new_chat(
            chat_data["chatCode"],
            chat_data["chatId"],
            user,
            "新建聊天",
            botName,
            botHandle,
            chat_data["botInfo"]["imgUrl"],
        )
        chatCode = chat_data["chatCode"]
        chat_id = chat_data["chatId"]
        new_chat = True
        # 把bot类型补上
        chat_data["botType"] = bot_type
        # 如果是自定义bot需要替换botName
        if bot_type == "自定义":
            chat_data["botInfo"]["botName"] = botName
            chat_data["botInfo"]["added"] = True
    # 获取消息id
    messageId = chat_data["messageNode"]["messageId"]
    # 更新最后对话时间
    await Chat.update_last_talk_time(user, chatCode)

    #################
    ### 回答环节
    #################
    return StreamingResponse(
        ai_reply(
            user,
            chatCode,
            chat_id,
            botName,
            botHandle,
            messageId,
            chat_data,
            new_chat,
            remain_points,
        ),
        media_type="text/event-stream",
        status_code=200,
    )


@router.post(
    "/talkAgain/{chatCode}",
    summary="重新回答，请求成功后需要重新拉取回答",
    description="messageId是要重新回答的id，price是这个bot的所需积分",
    responses={
        200: {
            "description": """
消息类型type有4种<br/>
humanMessageAdd -- 问题内容 <br/>
<br/>
botMessageAdd -- 回答内容 <br/>
<br/>
chatTitleUpdated -- 会话标题，只有新会话才有 <br/>
<br/>
talkError -- 回答出错 <br/>
""",
            "model": resp_models.BasicRespBody[resp_models.TalkRespBody],
        }
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    body: req_models.AnswerReqAgain = Body(
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

    bot_name, bot_handle, chat_id, title = await Chat.get_chat_info(user, chatCode)

    # 发起重新回答的请求
    try:
        await poe.client.answer_again(bot_handle, chatCode, messageId)
    except Exception as e:
        return response_500(repr(e))

    # 更新最后对话时间
    await Chat.update_last_talk_time(user, chatCode)

    #################
    ### 回答环节
    #################
    return StreamingResponse(
        ai_reply(
            user,
            chatCode,
            chat_id,
            bot_name,
            bot_handle,
            messageId,
            {},
            False,
            remain_points,
        ),
        media_type="text/event-stream",
        status_code=200,
    )


@router.post(
    "/answerStop/{chatCode}",
    summary="停止回答",
    description="写要停止回答的messageId",
    responses={
        200: {"description": "停止成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    chatCode: str = Path(description="chatCode", example="XXXYYY"),
    body: req_models.AnswerReqStop = Body(
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
        return response_500(repr(e))

    return response_200()


@router.delete(
    "/chatMemory/{chatCode}",
    summary="清除上下文记忆",
    responses={
        200: {
            "description": "响应一个消息节点，author为chat_break",
            "model": resp_models.BasicRespBody[resp_models.MessageNodeRespBody],
        }
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    bot_name, bot_handle, chat_id, title = await Chat.get_chat_info(user, chatCode)

    try:
        data = await poe.client.send_chat_break(chatCode, chat_id)
    except Exception as e:
        return response_500(repr(e))

    return response_200(data)


@router.delete(
    "/chat/{chatCode}",
    summary="删除会话",
    responses={
        200: {"description": "删除成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    chatCode: str = Path(description="chat code", example="XXXYYY"),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    bot_name, bot_handle, chat_id, title = await Chat.get_chat_info(user, chatCode)
    try:
        await poe.client.delete_chat(chatCode, chat_id)
    except Exception as e:
        return response_500(repr(e))

    await Chat.delete_chat(user, chatCode)
    user_action.info(f"用户 {user} {bot_name} ({bot_handle})  删除会话 {chatCode}")

    return response_200()


@router.post(
    "/translate",
    summary="翻译为中文",
    responses={
        200: {
            "description": "删除成功",
            "model": resp_models.BasicRespBody[resp_models.TranslateRespBody],
        },
    },
)
async def _(
    body: req_models.Translate = Body(
        examples=[
            {
                "text": "fuck you",
            }
        ],
    ),
    user_data: dict = Depends(verify_token),
):
    p_b, p_lat, formkey, proxy = await Config.get_setting()

    try:
        zh_text = (
            await Translator(proxies=proxy if proxy else None).translate(
                body.text, dest="zh-cn", src="auto"
            )
        ).text
    except Exception as e:
        return response_500(repr(e))

    return response_200({"zh_text": zh_text})
