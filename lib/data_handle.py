from poe_lib import Poe_Client
from random import choice
from string import ascii_letters, digits
from fastapi.responses import JSONResponse
from .db_model import Config
import logging

logger = logging.getLogger("uvicorn.error")


class Var:
    poe = Poe_Client("", "")


var = Var()


async def login_poe() -> JSONResponse:
    p_b, formkey, proxy = await Config.get_setting()
    if proxy:
        logger.info(f"使用代理连接Poe {proxy}")
    else:
        proxy = None
    try:
        var.poe = await Poe_Client(p_b, formkey, proxy).create()
        return JSONResponse({"code": 2000, "message": "success"}, 200)
    except Exception as e:
        msg = "poe ai 登陆失败。" + str(e)
        logger.error(msg)
        return JSONResponse({"code": 2000, "message": msg}, 500)


def generate_random_string():
    """生成随机字符串"""
    letters = ascii_letters + digits
    return "".join(choice(letters) for i in range(20))
