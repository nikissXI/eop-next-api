from .poe_lib import Poe_Client
from database import Config
from utils import *


class Poe:
    client = Poe_Client("", "")


poe = Poe()


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
