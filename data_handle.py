from async_poe_client import Poe_Client
from logging import getLogger
from random import choice
from string import ascii_letters, digits
from fastapi.responses import JSONResponse
from db_model import Config

logger = getLogger("uvicorn.error")


class Var:
    poe = Poe_Client("", "")


var = Var()


async def login_poe() -> JSONResponse:
    p_b, formkey, proxy = await Config.get_setting()
    try:
        var.poe = await Poe_Client(p_b, formkey, proxy).create()
        msg = "poe ai 登陆成功"
        logger.info(msg)
        return JSONResponse({"code": 2000, "message": "success"}, 200)
    except Exception as e:
        msg = "poe ai 登陆失败。" + str(e)
        logger.error(msg)
        return JSONResponse({"code": 2000, "message": msg}, 500)

    # "HbWywbzhu5baGOPgXctWEg%3D%3D",
    # "2cf0720596f3f7f81baff7890380e3f7",


def generate_random_string():
    """生成随机字符串"""
    letters = ascii_letters + digits
    return "".join(choice(letters) for i in range(20))


def handle_exception(err_msg: str) -> JSONResponse:
    """处理poe请求错误"""
    if "The bot doesn't exist or isn't accessible" in err_msg:
        return JSONResponse({"code": 6000, "message": "该会话已失效，请创建新会话"}, 500)

    logger.error(err_msg)
    return JSONResponse({"code": 6000, "message": err_msg}, 500)
