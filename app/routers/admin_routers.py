from utils import *
from services import *
from database import *
from utils.config import *
from models import *


router = APIRouter()


@router.post("/user/add", summary="增加用户")
async def _(
    body: AddUserBody = Body(
        example=[
            {"user": "username", "passwd": "password"},
        ]
    ),
    _: dict = Depends(verify_admin),
):
    msg = await User.create_user(body.user, body.passwd)
    if msg == "success":
        return JSONResponse({"code": 2000, "msg": "success"}, 200)

    return JSONResponse({"code": 2000, "msg": msg}, 500)


@router.delete("/{user}/delete", summary="删除用户")
async def _(
    user: str = Path(description="用户名", example="username"),
    _: dict = Depends(verify_admin),
):
    msg = await User.remove_user(user)
    if msg == "success":
        return JSONResponse({"code": 2000, "msg": "success"}, 200)

    return JSONResponse({"code": 2000, "msg": msg}, 500)


@router.get("/{user}/resetPasswd", summary="重置用户密码为一个新的随机密码")
async def _(
    user: str = Path(description="用户名", example="username"),
    _: dict = Depends(verify_admin),
):
    user_list = await User.list_user()
    if user not in user_list:
        return JSONResponse({"code": 2000, "msg": f"User {user} not found"}, 200)

    passwd = generate_random_password()
    await User.update_passwd(user, passwd)
    return JSONResponse({"code": 2000, "passwd": passwd}, 200)


@router.get("/loginPoe", summary="重新登录Poe")
async def _(_: dict = Depends(verify_admin)):
    return await login_poe()


@router.get("/listUser", summary="列出所有用户名")
async def _(_: dict = Depends(verify_admin)):
    data = await User.list_user()
    return JSONResponse({"code": 2000, "data": data}, 200)


@router.get("/getSetting", summary="获取配置，Poe的cookie和代理")
async def _(_: dict = Depends(verify_admin)):
    p_b, formkey, proxy = await Config.get_setting()
    return JSONResponse(
        {"code": 2000, "data": {"p_b": p_b, "formkey": formkey, "proxy": proxy}}, 200
    )


@router.patch("/updateSetting", summary="更新配置，Poe的cookie和代理")
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
    return JSONResponse({"code": 2000, "msg": "success"}, 200)
