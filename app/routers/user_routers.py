from hashlib import sha256
from io import BytesIO
from database import *
from models import *
from services import *
from utils import *
from utils.config import *

router = APIRouter()


@router.post("/login", summary="登陆接口", response_model=LoginResp)
async def _(
    body: LoginBody = Body(example={"user": "username", "passwd": "hashed_password"}),
):
    if not await User.check_user(body.user, body.passwd):
        return JSONResponse({"code": 2000, "msg": "Authentication failed"}, 401)

    token = create_token({"user": body.user})
    return JSONResponse({"access_token": token, "token_type": "Bearer"}, 200)


@router.get("/bots", summary="拉取用户可用bot")
async def _(user_data: dict = Depends(verify_token)):
    user = user_data["user"]
    botList = await User.get_user_botIdList(user)
    return JSONResponse({"code": 2000, "data": [botList]}, 200)


@router.put("/password", summary="修改密码")
async def _(
    body: UpdatePasswdBody = Body(
        example={"old_passwd": "jiu_mi_ma", "new_passwd": "xin_mi_ma"}
    ),
    user_data: dict = Depends(verify_token),
):
    user = user_data["user"]
    if not await User.check_user(user, body.old_passwd):
        return JSONResponse({"code": 2000, "msg": "Wrong password"}, 401)

    await User.update_passwd(user, body.new_passwd)
    return Response(status_code=204)


@router.get("/getPasswd", summary="生成密码哈希（临时）")
async def _(passwd: str = Query(description="明文密码", example="this_is_a_password")):
    hash_object = sha256()
    hash_object.update(passwd.encode("utf-8"))
    hash_value = hash_object.hexdigest()
    return hash_value
