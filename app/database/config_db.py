from tortoise import fields

from .db import Model


class Config(Model):
    key = fields.TextField(pk=True)
    value = fields.TextField()

    @classmethod
    async def init_data(cls):
        if not await cls.filter(key="p_b").exists():
            await cls.create(key="p_b", value="")
            await cls.create(key="p_lat", value="")
            await cls.create(key="formkey", value="")
            await cls.create(key="proxy", value="")
            await cls.create(key="telegram_url", value="")
            await cls.create(key="discord_url", value="")
            await cls.create(key="weixin_url", value="")
            await cls.create(key="qq_url", value="")

    @classmethod
    async def get_setting(cls) -> tuple[str, str, str, str, str, str, str, str]:
        rows = await cls.filter(key="p_b").values_list("value")
        p_b = rows[0][0]
        rows = await cls.filter(key="p_lat").values_list("value")
        p_lat = rows[0][0]
        rows = await cls.filter(key="formkey").values_list("value")
        formkey = rows[0][0]
        rows = await cls.filter(key="proxy").values_list("value")
        proxy = rows[0][0]
        rows = await cls.filter(key="telegram_url").values_list("value")
        telegram_url = rows[0][0]
        rows = await cls.filter(key="discord_url").values_list("value")
        discord_url = rows[0][0]
        rows = await cls.filter(key="weixin_url").values_list("value")
        weixin_url = rows[0][0]
        rows = await cls.filter(key="qq_url").values_list("value")
        qq_url = rows[0][0]
        return p_b, p_lat, formkey, proxy, telegram_url, discord_url, weixin_url, qq_url

    @classmethod
    async def update_setting(
        cls,
        p_b: str,
        p_lat: str,
        formkey: str,
        proxy: str,
        telegram_url: str,
        discord_url: str,
        weixin_url: str,
        qq_url: str,
    ):
        await cls.filter(key="p_b").update(value=p_b)
        await cls.filter(key="p_lat").update(value=p_lat)
        await cls.filter(key="formkey").update(value=formkey)
        await cls.filter(key="proxy").update(value=proxy)
        await cls.filter(key="telegram_url").update(value=telegram_url)
        await cls.filter(key="discord_url").update(value=discord_url)
        await cls.filter(key="weixin_url").update(value=weixin_url)
        await cls.filter(key="qq_url").update(value=qq_url)
