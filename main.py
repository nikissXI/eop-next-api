from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from async_poe_client import Poe_Client
from data_handle import var, logger

api_path = "/api"

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
    # 创建连接对象
    var.poe = await Poe_Client(
        "HbWywbzhu5baGOPgXctWEg%3D%3D",
        "2cf0720596f3f7f81baff7890380e3f7",
        proxy="http://127.0.0.1:7890",
    ).create()
    var.enable = True
    logger.info("poe ai on")

# 创建对话，bot_id由前端生成
@app.get(f"{api_path}/create")
async def _(bod_id: str):
    if var.enable is False:
        return Response({"msg": "poe未登录"}, 500)

    await var.poe.create_bot(
        handle=bod_id,
        prompt="You are the RoastMaster. You will respond to every user message with a spicy comeback. Do not use any swear or vulgar words in your responses.",
        suggested_replies=False,
    )
    return Response({"msg": "创建成功"})

# 对话，text就是问题
@app.get(f"{api_path}/talk")
async def _(bod_id: str, text: str):
    if var.enable is False:
        return Response({"msg": "poe未登录"}, 500)

    async def generate():
        async for message in var.poe.ask_stream(
            url_botname=bod_id,
            question=text,
            suggest_able=False,
        ):
            # print(message, end="")
            yield BytesIO(message.encode("utf-8")).read()

    return StreamingResponse(generate(), media_type="text/plain")

# 切换模型
@app.get(f"{api_path}/model")
async def _(bod_id: str, model: str):
    if var.enable is False:
        return Response({"msg": "poe未登录"}, 500)

    await var.poe.edit_bot(
        url_botname=bod_id,
        base_model=model,
    )
    return Response({"msg": "修改成功"})

# 切换预设
@app.get(f"{api_path}/prompt")
async def _(bod_id: str, prompt: str):
    if var.enable is False:
        return Response({"msg": "poe未登录"}, 500)

    await var.poe.edit_bot(
        url_botname=bod_id,
        prompt=prompt,
    )
    return Response({"msg": "修改成功"})

# 删除对话
@app.get(f"{api_path}/del")
async def _(bod_id: str):
    if var.enable is False:
        return Response({"msg": "poe未登录"}, 500)

    await var.poe.delete_bot(url_botname=bod_id)
    return Response({"msg": "删除成功"})

# 重置对话
@app.get(f"{api_path}/clear")
async def _(bod_id: str):
    if var.enable is False:
        return Response({"msg": "poe未登录"}, 500)

    await var.poe.delete_bot_conversation(url_botname=bod_id, del_all=True)
    await var.poe.send_chat_break(url_botname=bod_id)
    return Response({"msg": "清除成功"})


if __name__ == "__main__":
    from uvicorn import run

    run(app, host="0.0.0.0", port=8000)
