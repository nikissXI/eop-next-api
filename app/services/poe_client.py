from asyncio import sleep

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.config_db import Config
from fastapi import (
    Response,
)
from fastapi.responses import JSONResponse
from utils.tool_util import logger

try:
    pass
except Exception:
    pass

from .poe_lib.client import Poe_Client


class Poe:
    client = Poe_Client("", "", "")


poe = Poe()
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


@scheduler.scheduled_job("cron", minute=1)
async def _():
    while True:
        try:
            await poe.client.get_account_info()
            await sleep(10)
            await poe.client.cache_diy_model_list()
            await sleep(10)
            await poe.client.cache_offical_models()

        except Exception as e:
            logger.error(f"执行定时更新任务出错，10秒后重试，错误信息：{repr(e)}")
            await sleep(10)

        else:
            break


async def login_poe(
    p_b: str | None = None,
    p_lat: str | None = None,
    formkey: str | None = None,
    proxy: str | None = None,
) -> JSONResponse | Response:
    if not (p_b and p_lat and formkey and proxy):
        (
            p_b,
            p_lat,
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
        poe.client = await Poe_Client(p_b, p_lat, formkey, proxy).login()
        return Response(status_code=204)
    except Exception as e:
        msg = "执行登陆流程出错，" + repr(e)
        logger.error(msg)
        return JSONResponse({"code": 3008, "msg": msg}, 500)
