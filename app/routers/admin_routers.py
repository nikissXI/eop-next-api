from utils import *
from services import *
from database import *
from utils.config import *
from models import *


class UserNotExist(Exception):
    def __init__(self, user: str):
        self.user = user


async def check_user_exist(user: str):
    if not await User.user_exist(user):
        raise UserNotExist(user)


router = APIRouter()


@router.post(
    "/user/add",
    summary="增加用户",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "增加成功",
        },
    },
)
async def _(
    body: AddUserBody = Body(
        example={
            "user": "username",
            "passwd": "hashed_password",
            "expire_date": "2023-10-01",
            "admin": False,
        },
    ),
    _: dict = Depends(verify_admin),
):
    if await User.user_exist(body.user):
        return JSONResponse({"code": 2004, "msg": f"用户【{body.user}】已存在"}, 402)

    await User.create_user(body.user, body.passwd, body.expire_date, body.admin)
    return Response(status_code=204)


@router.delete(
    "/{user}/delete",
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
    user: str = Path(description="用户名", example="username"),
    _: dict = Depends(verify_admin),
):
    await check_user_exist(user)

    # 先把用户相关bot信息拉取并删除poe上的数据
    rows = await Bot.pre_remove_user_bots(user)
    for eop_id, diy, bot_id, chat_id in rows:
        try:
            if diy:
                handle, bot_id = await Bot.get_handle_and_bot_id(eop_id)
                await poe.client.delete_bot(handle, bot_id)

            else:
                handle, chat_id = await Bot.get_bot_handle_and_chat_id(eop_id)
                await poe.client.delete_chat_by_chat_id(handle, chat_id)
        except Exception as e:
            logger.error(f"删除相关bot时出错，错误信息：{e}")
    # 把数据库的相关bot信息删掉
    await Bot.remove_user_bots(user)
    # 把用户删掉
    await User.remove_user(user)
    return Response(status_code=204)


@router.patch(
    "/{user}/renew",
    summary="更新用户的过期日期",
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
    user: str = Path(description="用户名", example="username"),
    body: RenewUserBody = Body(
        example={
            "expire_date": "2023-10-01",
        }
    ),
    _: dict = Depends(verify_admin),
):
    await check_user_exist(user)

    await User.update_expire_date(user, body.expire_date)

    return Response(status_code=204)


@router.get(
    "/{user}/resetPasswd",
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
    user: str = Path(description="用户名", example="username"),
    _: dict = Depends(verify_admin),
):
    await check_user_exist(user)

    passwd, hashed_passwd = generate_random_password()
    await User.update_passwd(user, hashed_passwd)
    return JSONResponse({"passwd": passwd}, 200)


@router.get(
    "/loginPoe",
    summary="重新登录Poe",
    responses={
        200: {
            "description": "无相关响应",
        },
        204: {
            "description": "登陆成功",
        },
    },
)
async def _(_: dict = Depends(verify_admin)):
    return await login_poe()


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
                                "expire_date": "2023-01-01",
                                "admin": True,
                            },
                            {
                                "user": "user_B",
                                "expire_date": "2023-01-01",
                                "admin": False,
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
    for user, expire_date, admin in rows:
        data.append({"user": user, "expire_date": expire_date, "admin": admin})
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
                }
            },
        },
    },
)
async def _(_: dict = Depends(verify_admin)):
    p_b, formkey, proxy = await Config.get_setting()
    return JSONResponse({"p_b": p_b, "formkey": formkey, "proxy": proxy}, 200)


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
            "proxy": "",
        }
    ),
    _: dict = Depends(verify_admin),
):
    _p_b, _formkey, _proxy = await Config.get_setting()

    p_b = body.p_b if body.p_b else _p_b
    formkey = body.formkey if body.formkey else _formkey
    proxy = body.proxy if body.proxy else _proxy

    await Config.update_setting(p_b, formkey, proxy)
    return Response(status_code=204)
