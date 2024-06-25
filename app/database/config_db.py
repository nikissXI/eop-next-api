from tortoise import fields

from .db import Model


class Config(Model):
    key = fields.TextField(pk=True)
    value = fields.TextField()

    @classmethod
    async def init_data(cls):
        if await cls.all().first() is None:
            await cls.create(key="p_b", value="")
            await cls.create(key="p_lat", value="")
            await cls.create(key="formkey", value="")
            await cls.create(key="proxy", value="")

    @classmethod
    async def get_setting(cls) -> tuple[str, str, str, str]:
        p_b = (await cls.get(key="p_b")).value
        p_lat = (await cls.get(key="p_lat")).value
        formkey = (await cls.get(key="formkey")).value
        proxy = (await cls.get(key="proxy")).value

        return p_b, p_lat, formkey, proxy

    @classmethod
    async def update_setting(cls, p_b: str, p_lat: str, formkey: str, proxy: str):
        await cls.filter(key="p_b").limit(1).update(value=p_b)
        await cls.filter(key="p_lat").limit(1).update(value=p_lat)
        await cls.filter(key="formkey").limit(1).update(value=formkey)
        await cls.filter(key="proxy").limit(1).update(value=proxy)
