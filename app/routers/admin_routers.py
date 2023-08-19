from utils import *
from services import *
from database import *
from utils.config import *
from models import *


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
        example=[
            {"user": "username", "passwd": "password"},
        ]
    ),
    _: dict = Depends(verify_admin),
):
    user_list = await User.list_user()
    if body.user in user_list:
        return JSONResponse({"code": 2004, "msg": f"User {body.user} is exist"}, 500)

    msg = await User.create_user(body.user, body.passwd)
    if msg == "success":
        return Response(status_code=204)

    return JSONResponse({"code": 3001, "msg": msg}, 500)


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
    user_list = await User.list_user()
    if user not in user_list:
        return JSONResponse({"code": 2003, "msg": f"User {user} not found"}, 500)

    msg = await User.remove_user(user)
    if msg == "success":
        return Response(status_code=204)

    return JSONResponse({"code": 3001, "msg": msg}, 500)


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
    user_list = await User.list_user()
    if user not in user_list:
        return JSONResponse({"code": 2003, "msg": f"User {user} not found"}, 500)

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
    summary="列出所有用户名",
    responses={
        200: {
            "description": "用户名列表",
            "content": {"application/json": {"example": {"data": ["user_A, user_B"]}}},
        },
    },
)
async def _(_: dict = Depends(verify_admin)):
    data = await User.list_user()
    return JSONResponse({"data": data}, 200)


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
        examples=[
            {
                "p_b": "ABcdefz2u1baGdPgXxcWcg%3D%3D",
                "formkey": "2cf072difnsie23f7892divd0380e3f7",
                "proxy": "http://127.0.0.1:7890",
            },
            {
                "p_b": "ABcdefz2u1baGdPgXxcWcg%3D%3D",
                "formkey": "2cf072difnsie23f7892divd0380e3f7",
                "proxy": "",
            },
        ]
    ),
    _: dict = Depends(verify_admin),
):
    _p_b, _formkey, _proxy = await Config.get_setting()

    p_b = body.p_b if body.p_b else _p_b
    formkey = body.formkey if body.formkey else _formkey
    proxy = body.proxy if body.proxy else _proxy

    await Config.update_setting(p_b, formkey, proxy)
    return Response(status_code=204)
