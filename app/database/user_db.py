from tortoise import fields
from .db import Model


class User(Model):
    user = fields.TextField(pk=True)
    passwd = fields.TextField()
    admin = fields.BooleanField()

    @classmethod
    async def init_data(cls):
        if not await cls.filter(user="nikiss").exists():
            await cls.create(
                user="nikiss",
                passwd="f303aabb3a5bd6a547e3fdbf664bc7e093db187339048c74a0b19f8ebab42d3c",  # 明文nikiss，生产环境记得修改
                admin=True,
            )

    # 创建用户
    @classmethod
    async def create_user(cls, user: str, passwd: str, admin: bool):
        await cls.create(user=user, passwd=passwd, admin=admin)

    # 删除用户
    @classmethod
    async def remove_user(cls, user: str):
        await cls.filter(user=user).delete()

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
