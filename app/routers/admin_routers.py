from utils import *
from services import *
from database import *
from utils.config import *
from models import *


class UserNotExist(Exception):
    def __init__(self):
        pass


async def check_user_exist(uid: int):
    if not await User.user_exist(uid):
        raise UserNotExist()


router = APIRouter()


@router.post(
    "/user/add",
    summary="增加用户",
    responses={
        200: {
            "description": "返回用户uid",
            "content": {
                "application/json": {
                    "example": [
                        {"uid": "用户uid"},
                    ]
                }
            },
        },
    },
)
async def _(
    body: AddUserBody = Body(
        example={
            "user": "username",
            "passwd": "hashed_password",
            "level": 1,
            "expire_date": 1693230928703,
        },
    ),
    _: dict = Depends(verify_admin),
):
    if await User.user_exist(body.user):
        return JSONResponse({"code": 2004, "msg": f"用户【{body.user}】已存在"}, 402)

    await User.create_user(
        body.user,
        body.passwd,
        body.level,
        4070880000000 if body.level == 0 else body.expire_date,
    )
    uid = await User.get_uid(body.user)
    return JSONResponse({"uid": uid}, 200)


@router.delete(
    "/{uid}/delete",
    summary="删除用户",
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
    uid: int = Path(description="uid", example="1"),
    _: dict = Depends(verify_admin),
):
    await check_user_exist(uid)

    # 先把用户相关bot信息拉取并删除poe上的数据
    rows = await Bot.pre_remove_user_bots(uid)
    for eop_id, handle, diy, bot_id, chat_id in rows:
        try:
            if chat_id:
                await poe.client.delete_chat_by_chat_id(handle, chat_id)

            if diy:
                await poe.client.delete_bot(handle, bot_id)

        except Exception as e:
            logger.error(f"删除相关bot时出错，错误信息：{e}")
    # 把数据库的相关bot信息删掉
    await Bot.remove_user_bots(uid)
    # 把用户删掉
    await User.remove_user(uid)
    return Response(status_code=204)


@router.patch(
    "/{uid}/renew",
    summary="更新用户的级别和过期日期",
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
    uid: int = Path(description="uid", example="1"),
    body: RenewUserBody = Body(
        example={
            "level": 1,
            "expire_date": 1693230928703,
        }
    ),
    _: dict = Depends(verify_admin),
):
    await check_user_exist(uid)

    await User.update_info(uid, body.level, body.expire_date)

    return Response(status_code=204)


@router.get(
    "/{uid}/resetPasswd",
    summary="重置用户密码为一个新的随机密码",
    responses={
        200: {
            "description": "返回新密码",
            "content": {
                "application/json": {
                    "example": [
                        {"passwd": "新密码"},
                    ]
                }
            },
        },
    },
)
async def _(
    uid: int = Path(description="uid", example="1"),
    _: dict = Depends(verify_admin),
):
    await check_user_exist(uid)

    passwd, hashed_passwd = generate_random_password()
    await User.update_passwd(uid, hashed_passwd)
    return JSONResponse({"passwd": passwd}, 200)


@router.get(
    "/listUser",
    summary="列出所有用户",
    responses={
        200: {
            "description": "用户名列表",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {
                                "user": "user_A",
                                "uid": 1,
                                "level": 0,
                                "expire_date": 4070880000000,
                            },
                            {
                                "user": "user_B",
                                "uid": 2,
                                "level": 1,
                                "expire_date": 1693230928703,
                            },
                        ]
                    }
                }
            },
        },
    },
)
async def _(_: dict = Depends(verify_admin)):
    rows = await User.list_user()
    data = []
    for user, uid, level, expire_date in rows:
        data.append(
            {"user": user, "uid": uid, "level": level, "expire_date": expire_date}
        )
    return JSONResponse({"users": data}, 200)


@router.get(
    "/getSetting",
    summary="获取配置，Poe的cookie和代理",
    responses={
        200: {
            "description": "配置信息",
            "content": {
                "application/json": {
                    "p_b": "p_b值",
                    "formkey": "formkey值",
                    "proxy": "代理地址",
                    "telegram_url": "telegram群链接",
                    "discord_url": "discord群链接",
                    "weixin_url": "微信群链接",
                    "qq_url": "QQ群链接",
                }
            },
        },
    },
)
async def _(_: dict = Depends(verify_admin)):
    (
        p_b,
        formkey,
        proxy,
        telegram_url,
        discord_url,
        weixin_url,
        qq_url,
    ) = await Config.get_setting()
    return JSONResponse(
        {
            "p_b": p_b,
            "formkey": formkey,
            "proxy": proxy,
            "telegram_url": telegram_url,
            "discord_url": discord_url,
            "weixin_url": weixin_url,
            "qq_url": qq_url,
        },
        200,
    )


@router.patch(
    "/updateSetting",
    summary="修改配置，Poe的cookie和代理",
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
    body: UpdateSettingBody = Body(
        example={
            "p_b": "ABcdefz2u1baGdPgXxcWcg%3D%3D",
            "formkey": "2cf072difnsie23f7892divd0380e3f7",
            "proxy": "http://xxx",
            "telegram_url": "https://xxx",
            "discord_url": "https://xxx",
            "weixin_url": "https://xxx",
            "qq_url": "https://xxx",
        }
    ),
    _: dict = Depends(verify_admin),
):
    (
        _p_b,
        _formkey,
        _proxy,
        _telegram_url,
        _discord_url,
        _weixin_url,
        _qq_url,
    ) = await Config.get_setting()

    p_b = body.p_b if body.p_b else _p_b
    formkey = body.formkey if body.formkey else _formkey
    proxy = body.proxy if body.proxy else _proxy
    telegram_url = body.telegram_url if body.telegram_url else _telegram_url
    discord_url = body.discord_url if body.discord_url else _discord_url
    weixin_url = body.weixin_url if body.weixin_url else _weixin_url
    qq_url = body.qq_url if body.qq_url else _qq_url

    await Config.update_setting(
        p_b, formkey, proxy, telegram_url, discord_url, weixin_url, qq_url
    )

    if body.p_b or body.formkey or body.proxy:
        return await login_poe()

    return Response(status_code=204)


@router.get(
    "/accountInfo",
    summary="获取Poe账号信息以及限制模型使用情况",
    responses={
        200: {
            "description": "结果",
            "content": {
                "application/json": {
                    "example": {
                        "email": "xxx@gmail.com",
                        "subscription_actived": True,
                        "plan_type": "Monthly",
                        "expire_time": "1111-11-11 11:11:11",
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
    data["email"] = poe.client.user_info.email
    data["subscription_actived"] = poe.client.user_info.subscription_actived
    data["plan_type"] = ""
    data["expire_time"] = ""
    if poe.client.user_info.subscription_actived:
        data["plan_type"] = poe.client.user_info.plan_type
        data["expire_time"] = poe.client.user_info.expire_time
    return JSONResponse(data, 200)
