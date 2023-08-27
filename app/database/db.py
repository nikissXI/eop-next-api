from tortoise import Tortoise
from tortoise.connection import connections
from tortoise.models import Model as Model_

MODELS: list[str] = []


class Model(Model_):
    """
    自动添加模块
    Args:
        Model_ (_type_): _description_
    """

    def __init_subclass__(cls):
        MODELS.append(cls.__module__)


async def db_init():
    try:
        await Tortoise.init(db_url=f"sqlite://data.db", modules={"models": MODELS})
        await Tortoise.generate_schemas()
    except Exception as e:
        raise Exception(f"数据库连接错误... {type(e)}: {e}")


async def db_close():
    await connections.close_all()
