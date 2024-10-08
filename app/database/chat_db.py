from time import time

from tortoise import fields

from .db import Model


class Chat(Model):
    code = fields.TextField(pk=True)
    chat_id = fields.IntField()
    user = fields.TextField()
    title = fields.TextField()
    bot_name = fields.TextField()
    bot_handle = fields.TextField()
    img_url = fields.TextField()
    last_talk_time = fields.IntField()
    last_content = fields.TextField()

    @classmethod
    async def new_chat(
        cls,
        code: str,
        chat_id: int,
        user: str,
        title: str,
        bot_name: str,
        bot_handle: str,
        img_url: str,
    ):
        """新会话"""
        current_timestamp = int(time() * 1000)
        await cls.create(
            code=code,
            chat_id=chat_id,
            user=user,
            title=title,
            bot_name=bot_name,
            bot_handle=bot_handle,
            img_url=img_url,
            last_content="",
            last_talk_time=current_timestamp,
        )

    @classmethod
    async def get_chat_info(cls, user: str, code: str) -> tuple[str, str, int, str]:
        """获取chat信息"""
        _chat = await cls.get(user=user, code=code)
        return _chat.bot_name, _chat.bot_handle, _chat.chat_id, _chat.title

    @classmethod
    async def chat_exist(cls, user: str, chat_code: str) -> bool:
        """会话是否存在"""
        return await cls.filter(user=user, code=chat_code).limit(1).exists()

    @classmethod
    async def get_user_chat(
        cls, user: str, bot_handle: str = ""
    ) -> list[tuple[str, str, str, str, str, int, str, int]]:
        """获取用户的所有会话"""
        # 指定bot
        if bot_handle:
            return await cls.filter(user=user, bot_handle=bot_handle).values_list(
                "code",
                "title",
                "bot_name",
                "bot_handle",
                "img_url",
                "last_talk_time",
                "last_content",
                "chat_id",
            )

        return await cls.filter(user=user).values_list(
            "code",
            "title",
            "bot_name",
            "bot_handle",
            "img_url",
            "last_talk_time",
            "last_content",
            "chat_id",
        )

    @classmethod
    async def delete_chat(cls, user: str, code: str = ""):
        """删除会话"""
        if code:
            # 指定删哪个模型
            await cls.filter(user=user, code=code).limit(1).delete()
        else:
            # 某用户的所有模型
            await cls.filter(user=user).delete()

    @classmethod
    async def update_title(cls, user: str, code: str, title: str):
        """更新会话标题"""
        await cls.filter(user=user, code=code).limit(1).update(title=title)

    @classmethod
    async def update_last_talk_time(cls, user: str, code: str):
        """更新最后使用时间"""
        await (
            cls.filter(user=user, code=code)
            .limit(1)
            .update(last_talk_time=int(time() * 1000))
        )

    @classmethod
    async def update_last_content(cls, user: str, code: str, last_content: str):
        """更新最后对话内容"""
        await (
            cls.filter(user=user, code=code).limit(1).update(last_content=last_content)
        )

    @classmethod
    async def disable_chat(cls, user: str, code: str):
        """禁用会话"""
        await cls.filter(user=user, code=code).limit(1).update(disable=1)
