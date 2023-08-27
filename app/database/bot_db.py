from tortoise import fields
from .db import Model
from time import time


class Bot(Model):
    handle = fields.TextField(pk=True)
    bot_id = fields.IntField()
    chat_code = fields.TextField()
    chat_id = fields.IntField()
    user = fields.TextField()
    model = fields.TextField()
    alias = fields.TextField()
    prompt = fields.TextField()
    create_time = fields.IntField()
    last_talk_time = fields.IntField()

    # 创建bot
    @classmethod
    async def create_bot(
        cls,
        handle: str,
        bot_id: int,
        user: str,
        model: str,
        alias: str,
        prompt: str,
    ):
        current_timestamp = int(time())
        await cls.create(
            handle=handle,
            bot_id=bot_id,
            chat_code="",
            chat_id=0,
            user=user,
            model=model,
            alias=alias,
            prompt=prompt,
            create_time=current_timestamp,
            last_talk_time=current_timestamp,
        )

    # 获取某个用户的所有bot
    @classmethod
    async def get_user_bots(cls, user: str) -> list[dict]:
        rows = await cls.filter(user=user).values_list(
            "handle", "alias", "model", "prompt", "create_time", "last_talk_time"
        )
        data = []
        for handle, alias, model, prompt, create_time, last_talk_time in rows:
            data.append(
                {
                    "handle": handle,
                    "alias": alias,
                    "model": model,
                    "prompt": prompt,
                    "create_time": create_time,
                    "last_talk_time": last_talk_time,
                }
            )
        return data

    # 删除某个用户相关bot
    @classmethod
    async def remove_user_bots(cls, user: str):
        await cls.filter(user=user).delete()

    # 判断某个bot是否为该用户且存在
    @classmethod
    async def verify_bot(cls, user: str, handle: str) -> bool:
        return await cls.filter(user=user, handle=handle).exists()

    # 删除某个bot
    @classmethod
    async def delete_bot(cls, handle: str):
        await cls.filter(handle=handle).delete()

    # 更新某个bot的last_talk_time
    @classmethod
    async def update_bot_last_talk_time(cls, handle: str):
        await cls.filter(handle=handle).update(last_talk_time=int(time()))

    # 修改某个bot信息
    @classmethod
    async def modify_bot(
        cls,
        handle: str,
        model: str | None = None,
        alias: str | None = None,
        prompt: str | None = None,
    ):
        # 拉取旧数据
        rows = await cls.filter(handle=handle).values_list("model", "alias", "prompt")

        model = model or rows[0][0]
        alias = alias or rows[0][1]
        prompt = prompt or rows[0][2]

        await cls.filter(handle=handle).update(model=model, alias=alias, prompt=prompt)

    # 获取某个bot信息
    @classmethod
    async def get_bot_botId_model_prompt(cls, handle: str) -> tuple[int, str, str]:
        rows = await cls.filter(handle=handle).values_list("bot_id", "model", "prompt")
        return rows[0]

    # 获取某个bot的bot id
    @classmethod
    async def get_bot_id(cls, handle: str) -> int:
        rows = await cls.filter(handle=handle).values_list("bot_id")
        return rows[0][0]

    # 更新某个bot的chat code和chat id
    @classmethod
    async def update_bot_chat_code_and_chat_id(
        cls, handle: str, chat_code: str = "", chat_id: int = 0
    ):
        await cls.filter(handle=handle).update(chat_code=chat_code, chat_id=chat_id)

    # 获取某个bot的chat id
    @classmethod
    async def get_bot_chat_id(cls, handle: str) -> int:
        rows = await cls.filter(handle=handle).values_list("chat_id")
        return rows[0][0]

    # 列出所有bot id
    @classmethod
    async def list_all_handle(cls) -> list[str]:
        rows = await cls.filter().values_list("handle")
        data = []
        for handle in rows:
            data.append(handle)
        return data
