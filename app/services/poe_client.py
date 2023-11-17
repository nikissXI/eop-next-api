from .poe_lib import Poe_Client
from database import Config
from utils import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Poe:
    client = Poe_Client("", "")


poe = Poe()
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


@scheduler.scheduled_job("cron", hour=3)
async def _():
    poe.client.diy_displayName_list.clear()
    poe.client.offical_models.clear()
    await poe.client.cache_offical_models()


async def login_poe(
    p_b: str | None = None, formkey: str | None = None, proxy: str | None = None
) -> JSONResponse | Response:
    if not (p_b and formkey and proxy):
        (
            p_b,
            formkey,
            proxy,
            _,
            _,
            _,
            _,
        ) = await Config.get_setting()
    if proxy:
        logger.info(f"使用代理连接Poe {proxy}")
    else:
        proxy = None
    try:
        poe.client = await Poe_Client(p_b, formkey, proxy).login()
        return Response(status_code=204)
    except Exception as e:
        msg = "执行登陆流程出错，" + repr(e)
        logger.error(msg)
        return JSONResponse({"code": 3008, "msg": msg}, 500)
