from tortoise import fields

from .db import Model


class Bot(Model):
    user = fields.TextField()  # 所属用户
    bot_name = fields.TextField()  # 模型名称
    img_url = fields.TextField()  # 模型头像链接
    bot_type = fields.TextField()  # 模型类型  官方  自定义   第三方
    bot_handle = fields.TextField()  # Bot handle
    bot_id = fields.IntField()  # Bot id，某些时候用

    class Meta:
        table = "bot"

    @classmethod
    async def add_bot(
        cls,
        user: str,
        bot_name: str,
        img_url: str,
        bot_type: str,
        bot_handle: str,
        bot_id: int,
    ):
        """添加模型"""
        if not (await cls.filter(user=user, bot_handle=bot_handle).limit(1).exists()):
            await cls.create(
                user=user,
                bot_name=bot_name,
                img_url=img_url,
                bot_type=bot_type,
                bot_handle=bot_handle,
                bot_id=bot_id,
            )

    @classmethod
    async def bot_exist(cls, user: str, bot_handle: str) -> bool:
        return await cls.filter(user=user, bot_handle=bot_handle).limit(1).exists()

    @classmethod
    async def custom_bot_exist(cls, user: str, bot_name: str) -> bool:
        return (
            await cls.filter(user=user, bot_name=bot_name, bot_type="自定义")
            .limit(1)
            .exists()
        )

    @classmethod
    async def get_bot_info(cls, user: str, bot_handle: str) -> tuple[str, str, int]:
        """获取bot信息"""
        _bot = await cls.get(user=user, bot_handle=bot_handle)
        return _bot.bot_type, _bot.bot_name, _bot.bot_id

    @classmethod
    async def remove_bot(cls, user: str, bot_handle: str = ""):
        """删除模型"""
        if bot_handle:
            # 指定删哪个模型
            await cls.filter(user=user, bot_handle=bot_handle).limit(1).delete()
        else:
            # 某用户的所有模型
            await cls.filter(user=user).delete()

    @classmethod
    async def get_user_bot(cls, user: str) -> list[tuple[str, str, str, int, str]]:
        """获取用户模型列表"""
        return await cls.filter(user=user).values_list(
            "bot_name", "img_url", "bot_type", "bot_id", "bot_handle"
        )

    @classmethod
    async def update_bot_name(cls, user: str, bot_handle: str, bot_name: str):
        """更新botName"""
        await (
            cls.filter(user=user, bot_handle=bot_handle)
            .limit(1)
            .update(bot_name=bot_name)
        )
