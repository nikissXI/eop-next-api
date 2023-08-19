from tortoise import fields
from .db import Model


class User(Model):
    user = fields.TextField(pk=True)
    passwd = fields.TextField()
    admin = fields.BooleanField()
    botIdList = fields.TextField()

    @classmethod
    async def init_data(cls):
        if not await cls.filter(user="nikiss").exists():
            await cls.create(
                user="nikiss",
                passwd="200dac0c612e70b573dee52f7bb5732a4294ebda540f6d8979cffe267d6f5cb7",
                admin=True,
                botIdList="{}",
            )

    # 创建用户
    @classmethod
    async def create_user(cls, user: str, passwd: str, admin: bool) -> str:
        try:
            await cls.create(user=user, passwd=passwd, admin=admin, botIdList="{}")
            return "success"
        except Exception as e:
            return f"failed, reason: {repr(e)}"

    # 删除用户
    @classmethod
    async def remove_user(cls, user: str) -> str:
        try:
            await cls.filter(user=user).delete()
            return "success"
        except Exception as e:
            return f"failed, reason: {repr(e)}"

    # 修改用户密码
    @classmethod
    async def update_passwd(cls, user: str, newPasswd: str):
        await cls.filter(user=user).update(passwd=newPasswd)

    # 认证用户
    @classmethod
    async def check_user(cls, user: str, passwd: str) -> bool:
        if await cls.filter(user=user, passwd=passwd).exists():
            return True
        else:
            return False

    # 列出所有用户名
    @classmethod
    async def list_user(cls) -> dict[str, bool]:
        rows = await cls.filter().values_list("user", "admin")
        dd = {}
        for user, admin in rows:
            dd[user] = admin
        return dd

    # 判断是否为管理员
    @classmethod
    async def is_admin(cls, user: str) -> bool:
        rows = await cls.filter(user=user).values_list("admin")
        return rows[0][0]

    # 获取用户的botIdList
    @classmethod
    async def get_user_botIdList(cls, user: str) -> dict[str, tuple[str, str]]:
        rows = await cls.filter(user=user).values_list("botIdList")
        return eval(rows[0][0])

    # 增加用户的botIdList
    @classmethod
    async def update_user_botIdList(cls, user: str, botId: str, model: str, alias: str):
        botIdList = await cls.get_user_botIdList(user)
        botIdList[botId] = (model, alias)
        await cls.filter(user=user).update(botIdList=str(botIdList))

    # 删除用户的botIdList
    @classmethod
    async def del_user_botId(cls, user: str, botId: str):
        botIdList = await cls.get_user_botIdList(user)
        botIdList.pop(botId)
        await cls.filter(user=user).update(botIdList=str(botIdList))


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
