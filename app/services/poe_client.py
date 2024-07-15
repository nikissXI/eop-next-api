from time import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.config_db import Config
from database.user_db import User
from fastapi import Response
from fastapi.responses import JSONResponse
from utils.tool_util import logger, user_action

from .poe_lib.client import Poe_Client


class Poe:
    client = Poe_Client("", "", "")


poe = Poe()
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


# 每日0点10秒时检查重置时间
@scheduler.scheduled_job("cron", hour=0, minute=0, second=10)
async def _():
    now = int(time() * 1000)
    _users = await User.list_user()
    for _user in _users:
        user = _user.user
        monthPoints = _user.month_points
        resetDate = _user.reset_date
        expireDate = _user.expire_date
        # 如果账号过期就忽略
        if now > expireDate:
            continue
        # 如果还没到重置时间
        if now < resetDate:
            continue
        # 重置积分
        await User.update_remain_points(user, monthPoints)
        # 更新重置积分日期
        await User.update_reset_date(user, resetDate)
        logger.info(f"{user}重置可用积分为{monthPoints}")
        user_action.info(f"{user}重置可用积分为{monthPoints}")


async def login_poe(
    p_b: str | None = None,
    p_lat: str | None = None,
    formkey: str | None = None,
    proxy: str | None = None,
) -> str:
    if not (p_b and p_lat and formkey and proxy):
        (
            p_b,
            p_lat,
            formkey,
            proxy,
        ) = await Config.get_setting()
    if proxy:
        logger.info(f"使用代理连接Poe {proxy}")
    else:
        proxy = None
    try:
        poe.client = await Poe_Client(p_b, p_lat, formkey, proxy).login()
        return ""
    except Exception as e:
        err_msg = "执行登陆流程出错，" + repr(e)
        logger.error(err_msg)
        return err_msg
