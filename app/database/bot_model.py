from tortoise import fields
from .db import Model


class Bot(Model):
    bot_id = fields.TextField(pk=True)
    model = fields.TextField()
    alias = fields.TextField()
    prompot = fields.TextField()

    # 创建用户
    @classmethod
    async def create_bot(cls, bot_id: str, model: str, alias: str, prompot: str) -> str:
        try:
            await cls.create(bot_id=bot_id, model=model, alias=alias, prompot=prompot)
            return "success"
        except Exception as e:
            return f"failed, reason: {repr(e)}"

    # 删除用户
    @classmethod
    async def remove_bot(cls, bot_id: str) -> str:
        try:
            await cls.filter(bot_id=bot_id).delete()
            return "success"
        except Exception as e:
            return f"failed, reason: {repr(e)}"

    # 修改用户密码
    @classmethod
    async def update_bot(cls, user: str, newPasswd: str):
        await cls.filter(user=user).update(passwd=newPasswd)


    # 列出所有用户名
    @classmethod
    async def list_bots(cls) -> dict[str, bool]:
        rows = await cls.filter().values_list("user", "admin")
        dd = {}
        for user, admin in rows:
            dd[user] = admin
        return dd
