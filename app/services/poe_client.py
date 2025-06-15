from asyncio import create_task
from time import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.config_db import Config
from database.user_db import User
from utils.tool_util import logger, user_action

from .poe_lib.client import Poe_Client


class Poe:
    client = Poe_Client("", "", "")


poe = Poe()
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


@scheduler.scheduled_job("cron", hour=0, minute=0, second=10)
async def _():
    """每日0点10秒时检查重置时间"""
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


@scheduler.scheduled_job("cron", hour=3)
async def _():
    """每日3点更新hash"""
    await poe.client.update_hashes()
    # 取消之前的ws任务
    if poe.client.ws_client_task:
        poe.client.ws_client_task.cancel()
    # 创建ws任务
    poe.client.ws_client_task = create_task(poe.client.connect_to_channel())

    # 清空积分缓存
    poe.client.bot_price_cache.clear()


# 每日5点时清理队列内存
@scheduler.scheduled_job("cron", hour=5)
async def _():
    if poe.client.ws_client_task is None:
        poe.client.ws_data_queue.clear()


async def login_poe() -> str:
    p_b, p_lat, formkey, proxy = await Config.get_setting()
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
