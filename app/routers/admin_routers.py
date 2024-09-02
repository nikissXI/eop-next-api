import models.admin_req_models as req_models
import models.admin_resp_models as resp_models
from database.bot_db import Bot
from database.chat_db import Chat
from database.config_db import Config
from database.user_db import User
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Response,
)
from fastapi.responses import JSONResponse
from services.jwt_auth import verify_admin
from services.poe_client import login_poe, poe
from ujson import dump
from utils.env_util import gv
from utils.tool_util import generate_random_password, logger


def response_500(err_msg: str) -> JSONResponse:
    """500响应"""
    logger.error(err_msg)
    return JSONResponse({"code": 3001, "msg": err_msg, "data": None}, 500)


def response_200(data=None, status_code=200, msg: str = "success") -> Response:
    """200响应"""
    return JSONResponse(
        {"code": 0, "msg": msg, "data": data},
        status_code,
    )


router = APIRouter()


@router.get(
    "/users",
    summary="列出所有用户",
    responses={
        200: {
            "model": resp_models.BasicRespBody[list[resp_models.UserInfoRespBody]],
        }
    },
)
async def _(
    _verify: dict = Depends(verify_admin),
):
    user_list = []
    _users = await User.list_user()
    for _user in _users:
        user_list.append(
            {
                "user": _user.user,
                "remainPoints": _user.remain_points,
                "monthPoints": _user.month_points,
                "isAdmin": True if _user.admin else False,
                "resetDate": _user.reset_date,
                "expireDate": _user.expire_date,
            }
        )
    return response_200(user_list)


@router.post(
    "/user/add",
    summary="添加新用户",
    description="密码使用sha256加密，months就是有效期多少个月",
    responses={
        200: {
            "description": "增加成功",
            "model": resp_models.BasicRespBody[resp_models.UserInfoRespBody],
        }
    },
)
async def _(
    body: req_models.AddUserReqBody = Body(
        examples=[
            {
                "user": "username",
                "passwd": "sha256 Password",
                "monthPoints": 2000,
                "isAdmin": False,
                "months": 2,
            }
        ],
    ),
    _verify: dict = Depends(verify_admin),
):
    if await User.user_exist(body.user):
        return JSONResponse({"code": 2001, "msg": f"用户【{body.user}】已存在"}, 402)

    await User.create_user(
        body.user,
        body.passwd,
        body.monthPoints,
        1 if body.isAdmin else 0,
        666 if body.isAdmin else body.months,
    )

    user_info = await User.get_info(body.user)

    return response_200(
        {
            "user": user_info.user,
            "remainPoints": user_info.remain_points,
            "monthPoints": user_info.month_points,
            "isAdmin": 1 if user_info.admin else 0,
            "resetDate": user_info.reset_date,
            "expireDate": user_info.expire_date,
        },
    )


@router.delete(
    "/user/{user}",
    summary="删除用户",
    responses={
        200: {"description": "删除成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    user: str = Path(description="用户名", example="user_name"),
    _verify: dict = Depends(verify_admin),
):
    if not await User.user_exist(user):
        return JSONResponse({"code": 2001, "msg": "用户不存在"}, 402)
    # 删除用户的所有会话
    _rows = await Chat.get_user_chat(user)
    for row in _rows:
        try:
            await poe.client.delete_chat(row[0], row[7])
        except Exception as e:
            return response_500(repr(e))

    # 删除用户创建的bot
    _rows = await Bot.get_user_bot(user)
    for row in _rows:
        try:
            if row[2] == "自定义":
                await poe.client.delete_bot(row[4], row[3])

            if row[2] == "第三方":
                await poe.client.remove_bot(row[0], row[3])

        except Exception as e:
            return response_500(repr(e))

    await Chat.delete_chat(user)
    await Bot.remove_bot(user)
    # 把用户删掉
    await User.delete_user(user)

    return response_200()


@router.post(
    "/user/update",
    summary="更新用户信息",
    description="isAdmin字段，0是普通用户，1是管理员；addMonths是续多少个月，0就是不变",
    responses={200: {"model": resp_models.BasicRespBody[resp_models.UserInfoRespBody]}},
)
async def _(
    body: req_models.RenewUserReqBody = Body(
        examples=[
            {
                "user": "user_name",
                "remainPoints": 1000,
                "monthPoints": 2000,
                "isAdmin": False,
                "addMonths": 3,
            }
        ],
    ),
    _verify: dict = Depends(verify_admin),
):
    if not await User.user_exist(body.user):
        return JSONResponse({"code": 2001, "msg": "用户不存在"}, 402)
    await User.update_info(
        body.user, body.remainPoints, body.monthPoints, body.isAdmin, body.addMonths
    )

    user_info = await User.get_info(body.user)

    return response_200(
        {
            "user": user_info.user,
            "remainPoints": user_info.remain_points,
            "monthPoints": user_info.month_points,
            "isAdmin": 1 if user_info.admin else 0,
            "resetDate": user_info.reset_date,
            "expireDate": user_info.expire_date,
        },
    )


@router.get(
    "/user/resetPasswd/{user}",
    summary="重置用户密码为一个新的随机密码",
    responses={
        200: {"model": resp_models.BasicRespBody[resp_models.NewPasswdRespBody]}
    },
)
async def _(
    user: str = Path(description="user", examples=["user_name"]),
    _verify: dict = Depends(verify_admin),
):
    if not await User.user_exist(user):
        return JSONResponse({"code": 2001, "msg": "用户不存在"}, 402)

    passwd, hashedPasswd = generate_random_password()
    await User.update_passwd(user, hashedPasswd)

    return response_200(
        {
            "passwd": passwd,
        }
    )


@router.get(
    "/config",
    summary="获取poe账号配置和代理地址",
    responses={200: {"model": resp_models.BasicRespBody[resp_models.ConfigRespBody]}},
)
async def _(
    _verify: dict = Depends(verify_admin),
):
    p_b, p_lat, formkey, proxy = await Config.get_setting()

    return response_200(
        {
            "p_b": p_b,
            "p_lat": p_lat,
            "formkey": formkey,
            "proxy": proxy,
        },
    )


@router.post(
    "/config",
    summary="修改配置，Poe的cookie和代理",
    responses={
        200: {"description": "修改成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    body: req_models.UpdateSettingReqBody = Body(
        examples=[
            {
                "p_b": "ABcdefz2u1baGdPgXxcWcg%3D%3D",
                "p_lat": "ABcdefz2u1baGdPgXxcWcgY7YSQZ40dyWrO53FfQ%3D%3D",
                "formkey": "2cf072difnsie23f7892divd0380e3f7",
                "proxy": "http://xxx",
            }
        ]
    ),
    _verify: dict = Depends(verify_admin),
):
    await Config.update_setting(body.p_b, body.p_lat, body.formkey, body.proxy)
    if err_msg := await login_poe():
        return response_500(err_msg)

    return response_200()


@router.get(
    "/account",
    summary="获取Poe账号信息",
    responses={200: {"model": resp_models.BasicRespBody[resp_models.AccountRespBody]}},
)
async def _(
    _verify: dict = Depends(verify_admin),
):
    return response_200(await poe.client.get_account_info())


@router.post(
    "/hashUpload",
    summary="更新请求的hash（前端不用管）",
    responses={
        200: {"description": "更新成功", "model": resp_models.BasicRespBody[None]},
    },
)
async def _(
    body: req_models.HashUploadReqBody = Body(
        examples=[
            {
                "uploadKey": "upload_key",
                "queryHash": "data",
                "subHash": "data",
            }
        ],
    ),
):
    if body.uploadKey != gv.UPLOAD_KEY:
        return JSONResponse({"code": 2000, "msg": "upload_key error"}, 401)
    with open("services/poe_lib/query_hash.json", "w", encoding="utf-8") as w:
        dump(body.queryHash, w, indent=4)
    with open("services/poe_lib/sub_hash.json", "w", encoding="utf-8") as w:
        dump(body.subHash, w, indent=4)

    return response_200()


# @router.delete(
#     "/user/{botName}",
#     summary="测试接口",
#     responses={
#         200: {"description": "删除成功", "model": resp_models.BasicRespBody[None]},
#     },
# )
# async def _(
#     botName: str = Path(description="botName", example="ChatGPT"),
#     _verify: dict = Depends(verify_admin),
# ):
#     user = _verify["user"]
#     # 判断是否为自定义bot，如果是需要替换handle，handle为真实名称，并删除
#     try:
#         bot_type, bot_handle, bot_id = await Bot.get_bot_info(user, botName)
#         if bot_type == "自定义":
#             await poe.client.delete_bot(bot_handle, bot_id)

#         if bot_type == "第三方":
#             await poe.client.remove_bot(bot_handle, bot_id)

#     except Exception as e:
#         return response_500(repr(e))

#     return response_200()
