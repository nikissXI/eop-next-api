from tortoise import fields
from .db import Model
from datetime import date, datetime


class User(Model):
    user = fields.TextField(pk=True)
    passwd = fields.TextField()
    admin = fields.BooleanField()
    expire_date = fields.TextField()

    @classmethod
    async def init_data(cls):
        if not await cls.filter(user="nikiss").exists():
            await cls.create(
                user="nikiss",
                passwd="f303aabb3a5bd6a547e3fdbf664bc7e093db187339048c74a0b19f8ebab42d3c",  # 明文nikiss，生产环境记得修改
                expire_date="2099-01-01",
                admin=True,
            )

    # 创建用户
    @classmethod
    async def create_user(cls, user: str, passwd: str, expire_date: date, admin: bool):
        await cls.create(
            user=user, passwd=passwd, expire_date=str(expire_date), admin=admin
        )

    # 删除用户
    @classmethod
    async def remove_user(cls, user: str):
        await cls.filter(user=user).delete()

    # 修改用户密码
    @classmethod
    async def update_passwd(cls, user: str, newPasswd: str):
        await cls.filter(user=user).update(passwd=newPasswd)

    # 更新到期时间
    @classmethod
    async def update_expire_date(cls, user: str, expire_date: date):
        await cls.filter(user=user).update(expire_date=str(expire_date))

    # 用户是否存在
    @classmethod
    async def user_exist(cls, user: str) -> bool:
        return await cls.filter(user=user).exists()

    # 认证用户
    @classmethod
    async def check_user(cls, user: str, passwd: str) -> bool:
        return await cls.filter(user=user, passwd=passwd).exists()

    # 列出所有用户名
    @classmethod
    async def list_user(cls) -> list[tuple[str, str, bool]]:
        return await cls.filter().values_list("user", "expire_date", "admin")

    # 判断是否为管理员
    @classmethod
    async def is_admin(cls, user: str) -> bool:
        rows = await cls.filter(user=user).values_list("admin")
        return rows[0][0]

    # 判断是否过期
    @classmethod
    async def is_outdate(cls, user: str) -> bool:
        rows = await cls.filter(user=user).values_list("expire_date")
        expire_date = datetime.strptime(rows[0][0], "%Y-%m-%d").date()
        return expire_date < date.today()

    # 获取到期时间
    @classmethod
    async def get_expire_date(cls, user: str) -> str:
        rows = await cls.filter(user=user).values_list("expire_date")
        return rows[0][0]
