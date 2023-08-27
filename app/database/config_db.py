from tortoise import fields
from .db import Model


class Config(Model):
    key = fields.TextField(pk=True)
    value = fields.TextField()

    @classmethod
    async def init_data(cls):
        if not await cls.filter(key="p_b").exists():
            await cls.create(key="p_b", value="")
            await cls.create(key="formkey", value="")
            await cls.create(key="proxy", value="")

    @classmethod
    async def get_setting(cls) -> tuple[str, str, str]:
        rows = await cls.filter(key="p_b").values_list("value")
        p_b = rows[0][0]
        rows = await cls.filter(key="formkey").values_list("value")
        formkey = rows[0][0]
        rows = await cls.filter(key="proxy").values_list("value")
        proxy = rows[0][0]
        return p_b, formkey, proxy

    @classmethod
    async def update_setting(cls, p_b: str, formkey: str, proxy: str):
        await cls.filter(key="p_b").update(value=p_b)
        await cls.filter(key="formkey").update(value=formkey)
        await cls.filter(key="proxy").update(value=proxy)
