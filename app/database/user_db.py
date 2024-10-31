from datetime import datetime
from time import time

from dateutil.relativedelta import relativedelta
from tortoise import fields

from .db import Model


class User(Model):
    user = fields.TextField(pk=True)  # 用户名
    passwd = fields.TextField()  # 密码
    remain_points = fields.IntField()  # 可用积分
    month_points = fields.IntField()  # 总积分
    admin = fields.IntField()  # 是否为管理员
    reset_date = fields.IntField()  # 下一次重置积分日期
    expire_date = fields.IntField()  # 授权到期日期

    class Meta:
        table = "user"

    @classmethod
    async def init_data(cls):
        """如果用户列表里面为空，则进行初始化，创建一个admin管理员用户"""
        if await cls.all().first() is None:
            await cls.create(
                user="admin",
                passwd="8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # 明文admin，生产环境记得修改
                remain_points=200000,
                month_points=200000,
                admin=1,
                reset_date=int(
                    (datetime.now() + relativedelta(months=+1)).timestamp() * 1000
                ),
                expire_date=4070880000000,
            )

    @classmethod
    async def create_user(
        cls, user: str, passwd: str, month_points: int, admin: int, add_months: int
    ):
        """创建用户"""
        # 下一次重置时间
        reset_date = int((datetime.now() + relativedelta(months=+1)).timestamp() * 1000)
        # 过期时间
        expire_date = int(
            (datetime.now() + relativedelta(months=+add_months)).timestamp() * 1000
        )
        await cls.create(
            user=user,
            passwd=passwd,
            remain_points=month_points,
            month_points=month_points,
            admin=admin,
            reset_date=reset_date,
            expire_date=expire_date,
        )

    @classmethod
    async def delete_user(cls, user: str):
        """删除用户"""
        await (await cls.get(user=user)).delete()

    @classmethod
    async def update_passwd(cls, user: str, new_passwd: str):
        """修改用户密码"""
        await cls.filter(user=user).limit(1).update(passwd=new_passwd)

    @classmethod
    async def update_reset_date(cls, user: str, last_reset_date: int):
        """更新重置积分的日期"""
        # 过期时间，在之前的过期时间基础上加
        new_reset_date = int(
            (
                datetime.fromtimestamp(last_reset_date / 1000)
                + relativedelta(months=+1)
            ).timestamp()
            * 1000
        )
        await cls.filter(user=user).limit(1).update(reset_date=new_reset_date)

    @classmethod
    async def update_info(
        cls,
        user: str,
        remain_points: int,
        month_points: int,
        admin: int,
        add_months: int,
    ):
        """更新用户数据"""
        _user = await cls.get(user=user)
        if add_months != 0:
            # 已过期，就是当前时间比过期时间大
            if int(time() * 1000) > _user.expire_date:
                # 如果已过期的用户续就重置当前积分
                remain_points = month_points
                # 下一次重置时间
                reset_date = int(
                    (datetime.now() + relativedelta(months=+1)).timestamp() * 1000
                )
                # 过期时间
                expire_date = int(
                    (datetime.now() + relativedelta(months=+add_months)).timestamp()
                    * 1000
                )
            # 未过期
            else:
                # 下一次重置时间用原来的
                reset_date = _user.reset_date
                # 过期时间，在之前的过期时间基础上加
                expire_date = int(
                    (
                        datetime.fromtimestamp(_user.expire_date / 1000)
                        + relativedelta(months=+add_months)
                    ).timestamp()
                    * 1000
                )
        else:
            reset_date = _user.reset_date
            expire_date = _user.expire_date

        await (
            cls.filter(user=user)
            .limit(1)
            .update(
                remain_points=remain_points,
                month_points=month_points,
                admin=admin,
                reset_date=reset_date,
                expire_date=expire_date,
            )
        )

    @classmethod
    async def get_info(cls, user: str):
        """获取用户信息"""
        return await cls.get(user=user)

    @classmethod
    async def user_exist(cls, user: str) -> bool:
        """用户是否存在"""
        return await cls.filter(user=user).limit(1).exists()

    @classmethod
    async def auth_user(cls, user: str, passwd: str) -> bool:
        """验证账密"""
        return await cls.filter(user=user, passwd=passwd).limit(1).exists()

    @classmethod
    async def list_user(cls):
        """列出所有用户"""
        return await cls.all()

    @classmethod
    async def is_admin(cls, user: str) -> int:
        """是否为管理员"""
        _user = await cls.get(user=user)
        return _user.admin

    @classmethod
    async def is_outdate(cls, user: str) -> bool:
        """判断是否过期"""
        _user = await cls.get(user=user)
        return _user.expire_date < int(time() * 1000)

    @classmethod
    async def get_expire_date(cls, user: str) -> int:
        """获取授权到期时间"""
        _user = await cls.get(user=user)
        return _user.expire_date

    @classmethod
    async def get_remain_points(cls, user: str) -> int:
        """获取可用积分"""
        _user = await cls.get(user=user)
        return _user.remain_points

    @classmethod
    async def update_remain_points(cls, user: str, remain_points: int):
        """更新可用积分"""
        await cls.filter(user=user).limit(1).update(remain_points=remain_points)
