from io import BytesIO
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from data_handle import var, generate_random_string, handle_exception, login_poe
from jwt_handle import create_token, get_current_user
from db import db_init, db_disconnect
from db_model import Config, User

API_PATH = "/poe"
HOST = "0.0.0.0"
PORT = 23333

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


@app.post(f"{API_PATH}/login")
async def _(
    user: str | None = None,
    passwd: str | None = None,
):
    """
    用户登陆

    参数：
    user: 用户名
    passwd: 加密的密码

    返回值：
    accessToken: 登陆凭证，放在header里，Authorization : Bearer {accessToken}
    """
    if not (user and passwd):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    if await User.check_user(user, passwd):
        token = create_token({"user": user})
        return JSONResponse(
            {"code": 2000, "accessToken": token, "token_type": "Bearer"}, 200
        )

    return JSONResponse({"code": 2000, "message": "Authentication failed"}, 401)


@app.post(f"{API_PATH}/create")
async def _(
    model: str | None = None,
    prompt: str | None = None,
    botNick: str = "新会话",
    user_data: dict = Depends(get_current_user),
):
    """
    创建对话

    参数：
    model: 模型
    prompt: 预设
    botNick: 会话别名

    返回值：
    bot_id: 会话id
    """
    if not (model and prompt):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    user = user_data["user"]

    while True:
        try:
            bot_id = generate_random_string()
            await var.poe.create_bot(
                handle=bot_id,
                prompt=prompt,
                base_model=model,
                suggested_replies=False,
            )
            await User.add_user_botId(user, bot_id, botNick)
            return JSONResponse({"code": 2000, "bot_id": bot_id}, 200)

        except Exception as e:
            return handle_exception(str(e))


@app.post(f"{API_PATH}/talk")
async def _(bot_id: str, text: str, user_data: dict = Depends(get_current_user)):
    """
    对话

    参数：
    bot_id: 会话id
    text: 问题

    返回值：
    text: 答案
    """
    if not (bot_id and text):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:

        async def generate():
            async for message in var.poe.ask_stream(
                url_botname=bot_id,
                question=text,
                suggest_able=False,
            ):
                yield BytesIO(message.encode("utf-8")).read()

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/model")
async def _(bot_id: str, model: str, user_data: dict = Depends(get_current_user)):
    """
    切换模型

    参数：
    bot_id: 会话id
    model: 模型

    返回值：
    结果
    """
    if not (bot_id and model):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        await var.poe.edit_bot(url_botname=bot_id, base_model=model)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/prompt")
async def _(bot_id: str, prompt: str, user_data: dict = Depends(get_current_user)):
    """
    切换预设

    参数：
    bot_id: 会话id
    prompt: 预设

    返回值：
    结果
    """
    if not (bot_id and prompt):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        await var.poe.edit_bot(url_botname=bot_id, prompt=prompt)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/del")
async def _(bot_id: str, user_data: dict = Depends(get_current_user)):
    """
    删除对话

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    user = user_data["user"]

    if not bot_id:
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        await var.poe.delete_bot(url_botname=bot_id)
        await User.del_user_botId(user, bot_id)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/clear")
async def _(bot_id: str, user_data: dict = Depends(get_current_user)):
    """
    重置对话

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    if not bot_id:
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        await var.poe.delete_bot_conversation(url_botname=bot_id, del_all=True)
        await var.poe.send_chat_break(url_botname=bot_id)
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/history")
async def _(bot_id: str, user_data: dict = Depends(get_current_user)):
    """
    拉取聊天记录

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    if not bot_id:
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        messages = await var.poe.get_message_history(url_botname=bot_id, get_all=True)
        return JSONResponse({"code": 2000, "data": messages}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/info1")
async def _(bot_id: str, user_data: dict = Depends(get_current_user)):
    """
    拉取会话信息1

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    if not bot_id:
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        data = await var.poe.get_botdata(url_botname=bot_id)
        return JSONResponse({"code": 2000, "data": data}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/info2")
async def _(bot_id: str, user_data: dict = Depends(get_current_user)):
    """
    拉取会话信息2

    参数：
    bot_id: 会话id

    返回值：
    结果
    """
    if not bot_id:
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    try:
        data = await var.poe.get_bot_info(url_botname=bot_id)
        return JSONResponse({"code": 2000, "data": data}, 200)

    except Exception as e:
        return handle_exception(str(e))


@app.get(f"{API_PATH}/getBotList")
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


################
##################  下方为管理接口
####################


@app.get(f"{API_PATH}/loginPoe")
async def _(user_data: dict = Depends(get_current_user)):
    """
    重新登录poe

    返回值：
    结果
    """
    if user_data["user"] != "nikiss":
        return JSONResponse({"code": 2000, "message": "forbidden"}, 403)

    return await login_poe()


@app.get(f"{API_PATH}/getSetting")
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


@app.post(f"{API_PATH}/updateSetting")
async def _(
    p_b: str, formkey: str, proxy: str, user_data: dict = Depends(get_current_user)
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

    if not (p_b and formkey and proxy):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    await Config.update_setting(p_b, formkey, proxy)
    return JSONResponse({"code": 2000, "message": "success"}, 200)


@app.post(f"{API_PATH}/addUser")
async def _(user: str, passwd: str, user_data: dict = Depends(get_current_user)):
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

    if not (user and passwd):
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    msg = await User.create_user(user, passwd)
    if msg == "success":
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    return JSONResponse({"code": 2000, "message": msg}, 500)


@app.get(f"{API_PATH}/delUser")
async def _(user: str, user_data: dict = Depends(get_current_user)):
    """
    删除用户

    参数：
    user: 用户名

    返回值：
    结果
    """
    if user_data["user"] != "nikiss":
        raise HTTPException(status_code=403, detail="Forbidden")

    if not user:
        return JSONResponse({"code": 2000, "message": "Missing parameters"}, 400)

    msg = await User.remove_user(user)
    if msg == "success":
        return JSONResponse({"code": 2000, "message": "success"}, 200)

    return JSONResponse({"code": 2000, "message": msg}, 500)


@app.get(f"{API_PATH}/listUser")
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


if __name__ == "__main__":
    from uvicorn import run

    run(app, host=HOST, port=PORT)
