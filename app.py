from io import BytesIO
from fastapi import Depends, FastAPI, HTTPException, Request, Query
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from lib.data_handle import var, generate_random_string, login_poe, logger
from lib.jwt_handle import create_token, get_current_user
from lib.db import db_init, db_disconnect
from lib.db_model import Config, User
from fastapi.exceptions import RequestValidationError

##############################
###### 预处理
##############################

API_PATH = "/poe"
HOST = "0.0.0.0"
PORT = 80

app = FastAPI()


# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _():
    await db_init()
    await User.init_data()
    await Config.init_data()
    await login_poe()


@app.on_event("shutdown")
async def _():
    await db_disconnect()


##############################
###### 异常捕获
##############################


@app.exception_handler(RequestValidationError)
async def _(request: Request, exc: RequestValidationError):
    if isinstance(exc.errors(), list):
        if (
            exc.errors()[0]["type"] == "missing"
            and exc.errors()[0]["msg"] == "Field required"
        ):
            return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    return JSONResponse({"code": "2000", "message": exc.errors()}, 400)


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    if "The bot doesn't exist or isn't accessible" in err_msg:
        return JSONResponse({"code": 6000, "message": "该会话已失效，请创建新会话"}, 500)

    logger.error(err_msg)
    return JSONResponse({"code": 6000, "message": err_msg}, 500)


##############################
###### 用户路由
##############################


@app.post(f"{API_PATH}/login")
async def login(
    user: str,
    passwd: str,
):
    """
    用户登陆

    参数：
    user: 用户名
    passwd: 加密的密码

    返回值：
    accessToken: 登陆凭证，放在header里，Authorization : Bearer {accessToken}
    """
    if await User.check_user(user, passwd):
        token = create_token({"user": user})
        return JSONResponse(
            {"access_token": token, "token_type": "Bearer"}, 200
        )

    return JSONResponse({"code": 2000, "message": "Authentication failed"}, 401)


@app.post(f"{API_PATH}/bot")
async def create_bot(
    model: str,
    prompt: str = "You are a large language model. Follow the user's instructions carefully.",
    botNick: str = "新会话",
    user_data: dict = Depends(get_current_user),
):
    """
    创建对话

    参数：
    model: 模型，无次数限制模型：ChatGPT、Claude，有次数限制模型：ChatGPT4、Claude-2-100k
    prompt: 预设
    botNick: 会话别名

    返回值：
    bot_id: 会话id
    """
    model_dict = {
        "ChatGPT": "chinchilla",
        "Claude": "a2",
        "ChatGPT4": "beaver",
        "Claude-2-100k": "a2_2",
    }

    if model not in model_dict:
        return JSONResponse({"code": 2000, "message": "Wrong model"}, 402)

    user = user_data["user"]

    while True:
        try:
            bot_id = generate_random_string()
            await var.poe.create_bot(
                handle=bot_id,
                prompt=prompt,
                base_model=model_dict[model],
                suggested_replies=False,
            )
            await User.add_user_botId(user, bot_id, botNick)
            return JSONResponse({"bot_id": bot_id}, 200)

        except Exception as e:
            return handle_exception(str(e))


@app.delete(f"{API_PATH}/bot/{bot_id}")
async def delete_bot(
    bot_id: str,
    user_data: dict = Depends(get_current_user),
):
    """
    删除对话

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    user = user_data["user"]

    try:
        await var.poe.delete_bot(url_botname=bot_id)
        await User.del_user_botId(user, bot_id)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.post(f"{API_PATH}/talk")
async def ask_question(
    bot_id: str,
    q: str,
    user_data: dict = Depends(get_current_user),
):
    """
    对话

    参数：
    bot_id: 会话id
    q: 问题

    返回值：
    text: 答案
    """
    try:

        async def generate():
            async for message in var.poe.ask_stream(
                url_botname=bot_id,
                question=q,
                suggest_able=False,
            ):
                yield BytesIO(message.encode("utf-8")).read()

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        return handle_exception(str(e))


@app.put(f"{API_PATH}/{bot_id}/model")
async def modify_model(
    bot_id: str,
    model: str,
    user_data: dict = Depends(get_current_user),
):
    """
    切换模型

    参数：
    bot_id: 会话id
    model: 模型

    返回值：
    结果
    """
    try:
        await var.poe.edit_bot(url_botname=bot_id, base_model=model)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.put(f"{API_PATH}/{bot_id}/prompt")
async def modify_prompt(
    bot_id: str,
    prompt: str,
    user_data: dict = Depends(get_current_user),
):
    """
    切换预设

    参数：
    bot_id: 会话id
    prompt: 预设

    返回值：
    结果
    """
    try:
        await var.poe.edit_bot(url_botname=bot_id, prompt=prompt)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.put(f"{API_PATH}/bot/{bot_id}/clear_msg")
async def clear_bot_msg(
    bot_id: str,
    user_data: dict = Depends(get_current_user),
):
    """
    重置对话

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    try:
        await var.poe.delete_bot_conversation(url_botname=bot_id, del_all=True)
        await var.poe.send_chat_break(url_botname=bot_id)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/bot/{bot_id}/history")
async def get_bot_msg(
    bot_id: str,
    limit: int = Query(default=50, description="Number of messages to retrieve"),
    before_msg_id: Optional[str] = Query(None, description="Retrieve messages before this message ID"),
    after_msg_id: Optional[str] = Query(None, description="Retrieve messages after this message ID"),
    user_data: dict = Depends(get_current_user),
):
    """
    拉取历史聊天记录

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    try:
        messages = await var.poe.get_message_history(url_botname=bot_id, get_all=True)
        return JSONResponse({"code": 2000, "data": messages}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/bot/{bot_id}/info")
async def _(
    bot_id: str,
    user_data: dict = Depends(get_current_user),
):
    """
    拉取会话信息

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    try:
        data = await var.poe.get_botdata(url_botname=bot_id)
        return JSONResponse({"data": data}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/user/bots")
async def _(user_data: dict = Depends(get_current_user)):
    """
    拉取用户可用bot

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    user = user_data["user"]

    botList = await User.get_user_botIdList(user)
    return JSONResponse({"code": 2000, "data": botList}, 200)


@app.put(f"{API_PATH}/user/password")
async def _(
    old_passwd: str,
    new_passwd: str,
    user_data: dict = Depends(get_current_user),
):
    """
    修改用户密码

    参数：
        old_passwd: 旧密码
        new_passwd: 新密码

    返回值：
        结果
    """
    user = user_data["user"]

    if not await User.check_user(user, old_passwd):
        return JSONResponse({"code": 2000, "message": "Wrong password"}, 401)

    await User.update_passwd(user, new_passwd)
    return JSONResponse({"code": 2000, "message": "success"}, 200)


################
##################  下方为管理接口
####################


@app.get(f"{API_PATH}/admin/loginPoe")
async def _(user_data: dict = Depends(get_current_user)):
    """
    重新登录poe

    返回值：
    结果
    """
    if user_data["user"] != "nikiss":
        return JSONResponse({"code": 2000, "message": "forbidden"}, 403)

    return await login_poe()


@app.get(f"{API_PATH}/admin/getSetting")
async def _(user_data: dict = Depends(get_current_user)):
    """
    获取配置，poe的cookie和代理

    返回值：
    结果
    """
    if user_data["user"] != "nikiss":
        return JSONResponse({"code": 2000, "message": "forbidden"}, 403)

    p_b, formkey, proxy = await Config.get_setting()
    return JSONResponse(
        {"code": 2000, "data": {"p_b": p_b, "formkey": formkey, "proxy": proxy}}, 200
    )


@app.post(f"{API_PATH}/admin/updateSetting")
async def _(
    p_b: str = "",
    formkey: str = "",
    proxy: str = "",
    user_data: dict = Depends(get_current_user),
):
    """
    更新配置，poe的cookie和代理

    参数：
    p_b: p_b
    formkey: formkey
    proxy: 代理

    返回值：
    结果
    """
    if user_data["user"] != "nikiss":
        return JSONResponse({"code": 2000, "message": "forbidden"}, 403)

    _p_b, _formkey, _proxy = await Config.get_setting()

    p_b = p_b if p_b else _p_b
    formkey = formkey if formkey else _formkey
    proxy = proxy if proxy else _proxy

    await Config.update_setting(p_b, formkey, proxy)
    return JSONResponse({"code": 2000, "message": "success"}, 200)


@app.post(f"{API_PATH}/admin/addUser")
async def _(
    user: str,
    passwd: str,
    user_data: dict = Depends(get_current_user),
):
    """
    增加用户

    参数：
    user: 用户名
    passwd: 加密的密码

    返回值：
    结果
    """
    if user_data["user"] != "nikiss":
        return JSONResponse({"code": 2000, "message": "forbidden"}, 403)

    msg = await User.create_user(user, passwd)
    if msg == "success":
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    return JSONResponse({"code": 2000, "message": msg}, 500)


@app.get(f"{API_PATH}/admin/delUser")
async def _(
    user: str,
    user_data: dict = Depends(get_current_user),
):
    """
    删除用户

    参数:
        user: 用户名

    返回值:
        结果
    """
    if user_data["user"] != "nikiss":
        raise HTTPException(status_code=403, detail="Forbidden")

    msg = await User.remove_user(user)
    if msg == "success":
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    return JSONResponse({"code": 2000, "message": msg}, 500)


@app.get(f"{API_PATH}/admin/listUser")
async def _(user_data: dict = Depends(get_current_user)):
    """
    列出所有用户

    返回值：
        结果
    """
    if user_data["user"] != "nikiss":
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await User.list_user()
    return JSONResponse({"code": 2000, "data": data}, 200)


@app.get(f"{API_PATH}/admin/accountInfo")
async def _(user_data: dict = Depends(get_current_user)):
    """
    查询账号信息

    返回值：
        结果
    """
    if user_data["user"] != "nikiss":
        raise HTTPException(status_code=403, detail="Forbidden")

    data = var.poe.subscription
    return JSONResponse({"code": 2000, "data": data}, 200)


if __name__ == "__main__":
    from uvicorn import run

    custom_logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s - %(levelprefix)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s - %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    run(app, host=HOST, port=PORT, log_config=custom_logging_config)
