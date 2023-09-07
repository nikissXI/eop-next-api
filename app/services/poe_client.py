from .poe_lib import Poe_Client
from database import Config
from utils import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from re import sub
from asyncio import create_task


class Poe:
    client = Poe_Client("", "")


poe = Poe()


async def login_poe() -> JSONResponse | Response:
    p_b, formkey, proxy = await Config.get_setting()
    if proxy:
        logger.info(f"使用代理连接Poe {proxy}")
    else:
        proxy = None
    try:
        poe.client = await Poe_Client(p_b, formkey, proxy).login()
        return Response(status_code=204)
    except Exception as e:
        msg = "执行登陆流程出错，" + str(e)
        logger.error(msg)
        return JSONResponse({"code": 3008, "msg": msg}, 500)


scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


# 刷新ws地址
@scheduler.scheduled_job("interval", seconds=1)
async def _():
    if (
        poe.client.ws_client_task == None
        or poe.client.refresh_channel_lock == True
        or poe.client.talking
    ):
        return
    # 120秒没对话就重连ws
    poe.client.refresh_ws_cd -= 1

    if poe.client.refresh_ws_cd <= 0:
        poe.client.refresh_ws_cd = 120
        poe.client.refresh_channel_count += 1
        poe.client.channel_url = sub(
            r"(min_seq=)\d+",
            r"\g<1>" + str(poe.client.last_min_seq),
            poe.client.channel_url,
        )
        get_new_channel = True if poe.client.refresh_channel_count > 60 else False
        create_task(poe.client.refresh_channel(get_new_channel))
