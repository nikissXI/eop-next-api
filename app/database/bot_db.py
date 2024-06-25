from tortoise import fields

from .db import Model


class Bot(Model):
    user = fields.TextField()  # 所属用户
    name = fields.TextField()  # 模型名称
    img_url = fields.TextField()  # 模型头像链接
    bot_type = fields.TextField()  # 模型类型  官方  自定义   第三方
    bot_handle = fields.TextField()  # Bot handle，某些时候用 todo，如果用不上就删了
    bot_id = fields.IntField()  # Bot id，某些时候用

    class Meta:
        table = "bot"

    @classmethod
    async def add_bot(
        cls,
        user: str,
        name: str,
        img_url: str,
        bot_type: str,
        bot_handle: str,
        bot_id: int,
    ):
        """添加模型"""
        if not await cls.bot_exist(user, name):
            await cls.create(
                user=user,
                name=name,
                img_url=img_url,
                bot_type=bot_type,
                bot_handle=bot_handle,
                bot_id=bot_id,
            )

    @classmethod
    async def bot_exist(cls, user: str, name: str) -> bool:
        return await cls.filter(user=user, name=name).limit(1).exists()

    @classmethod
    async def get_bot_info(cls, user: str, name: str) -> tuple[str, str, int]:
        """获取bot信息"""
        _user = await cls.get(user=user, name=name)
        return _user.bot_type, _user.bot_handle, _user.bot_id

    @classmethod
    async def remove_bot(cls, user: str, name: str = ""):
        """删除模型"""
        if name:
            # 指定删哪个模型
            await cls.filter(user=user, name=name).limit(1).delete()
        else:
            # 某用户的所有模型
            await cls.filter(user=user).delete()

    @classmethod
    async def get_user_bot(cls, user: str) -> list[tuple[str, str, str, int]]:
        """获取用户模型列表"""
        return await cls.filter(user=user).values_list(
            "name", "img_url", "bot_type", "bot_id"
        )

    @classmethod
    async def update_botName(cls, user: str, bot_id: int, name: str):
        """更新botName"""
        await cls.filter(user=user, bot_id=bot_id).limit(1).update(name=name)
