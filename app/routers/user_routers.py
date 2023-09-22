from hashlib import sha256
from database import *
from models import *
from services import *
from utils import *
from utils.config import *

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
