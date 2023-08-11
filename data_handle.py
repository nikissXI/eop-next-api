from async_poe_client import Poe_Client
from logging import getLogger


logger = getLogger("uvicorn.error")


class Var:
    poe = Poe_Client("")
    enable = False
    p_b = ""
    formkey = ""
    proxy = ""


var = Var()


async def login_poe() -> str:
    try:
        var.poe = await Poe_Client(
            var.p_b,
            var.formkey,
            proxy=var.proxy,
        ).create()
        msg = "poe ai 登陆成功！"
        logger.info(msg)
    except Exception as e:
        err_msg = str(e)
        if (
            "Failed to extract 'viewer' or 'user_id' from 'next_data'." in err_msg
            or "Failed to get basedata from home." in err_msg
        ):
            msg = "登陆凭证无效"
        else:
            msg = "poe ai 登陆失败：" + str(e)
        logger.error(msg)

    return msg
