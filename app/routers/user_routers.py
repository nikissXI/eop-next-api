from hashlib import sha256

from database.bot_db import Bot as Bot
from database.chat_db import Chat as Chat
from database.config_db import Config as Config
from database.db import db_close as db_close
from database.db import db_init as db_init
from database.user_db import User as User
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Query,
    Response,
)
from fastapi.responses import JSONResponse
from models.user_models import (
    LoginBody,
    UpdatePasswdBody,
)
from services.jwt_auth import create_token, verify_token
from services.poe_client import poe

router = APIRouter()


@router.post(
    "/login",
    summary="登陆接口",
    responses={
        200: {
            "description": "登陆成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbxxxxxxxxxxxxxxxxxxxxxxxx",
                        "token_type": "Bearer",
                    }
                }
            },
        },
    },
)
async def _(
    body: LoginBody = Body(examples=[{"user": "用户名", "passwd": "加密后的密码"}]),
):
    if not await User.check_user(body.user, body.passwd):
        return JSONResponse({"code": 2000, "msg": "认证失败"}, 401)

    uid = await User.get_uid(body.user)
    token = create_token({"uid": uid})
    return JSONResponse({"access_token": token, "token_type": "Bearer"}, 200)


@router.get(
    "/info",
    summary="获取用户信息，包含是否为管理员以及过期日期",
    responses={
        200: {
            "description": "用户信息",
            "content": {
                "application/json": {
                    "example": {
                        "user": "user_name",
                        "uid": 114514,
                        "level": 1,
                        "expire_date": 4070880000000,
                    }
                }
            },
        },
    },
)
async def _(user_data: dict = Depends(verify_token)):
    uid = user_data["uid"]
    user, uid, level, expire_date = (await User.list_user(uid))[0]

    return JSONResponse(
        {"user": user, "uid": uid, "level": level, "expire_date": expire_date}, 200
    )


@router.put(
    "/password",
    summary="修改密码",
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
    body: UpdatePasswdBody = Body(
        example={"old_passwd": "加密的旧密码", "new_passwd": "加密的新密码"}
    ),
    user_data: dict = Depends(verify_token),
):
    uid = user_data["uid"]

    user, uid, level, expire_date = (await User.list_user(uid))[0]
    # test不能让用户自己改密码
    if user == "test":
        return Response(status_code=204)

    if not await User.check_user(user, body.old_passwd):
        return JSONResponse({"code": 2000, "msg": "密码错误"}, 401)

    await User.update_passwd(uid, body.new_passwd)
    return Response(status_code=204)


@router.get("/getPasswd", summary="生成密码哈希（临时）")
async def _(passwd: str = Query(description="明文密码", example="this_is_a_password")):
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    hash_value = hash_object.hexdigest()
    return hash_value


@router.get(
    "/bots",
    summary="拉取用户可用会话",
    responses={
        200: {
            "description": "会话列表",
            "content": {
                "application/json": {
                    "example": {
                        "bots": [
                            {
                                "eop_id": "114514",
                                "alias": "AAA",
                                "model": "ChatGPT",
                                "prompt": "prompt_A",
                                "image": "https://xxx",
                                "create_time": 1693230928703,
                                "last_talk_time": 1693230928703,
                                "disable": False,
                            },
                            {
                                "eop_id": "415411",
                                "alias": "BBB",
                                "model": "ChatGPT4",
                                "prompt": "",
                                "image": "https://xxx",
                                "create_time": 1693230928703,
                                "last_talk_time": 1693230928703,
                                "disable": True,
                            },
                        ]
                    }
                }
            },
        },
    },
)
async def _(user_data: dict = Depends(verify_token)):
    uid = user_data["uid"]
    botList = await Chat.get_user_bot(uid)
    return JSONResponse({"bots": botList}, 200)


@router.get(
    "/LimitedModelsInfo",
    summary="获取模型次数刷新时间以及限制模型使用情况",
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
                                "limit_type": "hard_limit",
                                "available": True,
                                "daily_available_times": 30,
                                "daily_total_times": 30,
                                "monthly_available_times": 1030,
                                "monthly_total_times": 1030,
                            },
                            {
                                "model": "GPT-4",
                                "limit_type": "soft_limit",
                                "available": True,
                                "daily_available_times": 1,
                                "daily_total_times": 1,
                                "monthly_available_times": 592,
                                "monthly_total_times": 601,
                            },
                        ],
                        "daily_refresh_time": 1693230928703,
                        "monthly_refresh_time": 1693230928703,
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
