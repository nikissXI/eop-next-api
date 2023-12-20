from random import randint
from time import time

from tortoise import fields

from .db import Model


class Chat(Model):
    eop_id = fields.TextField(pk=True)
    uid = fields.IntField()
    diy = fields.BooleanField()
    handle = fields.TextField()
    bot_id = fields.IntField()
    chat_id = fields.IntField()
    display_name = fields.TextField()
    alias = fields.TextField()
    prompt = fields.TextField()
    image_link = fields.TextField()
    create_time = fields.IntField()
    last_talk_time = fields.IntField()
    disable = fields.BooleanField(default=0)

    # eop id是否存在
    @classmethod
    async def eop_id_exist(cls, eop_id: str) -> bool:
        return await cls.filter(eop_id=eop_id).exists()

    # 创建bot
    @classmethod
    async def create_bot(
        cls,
        uid: int,
        diy: bool,
        handle: str,
        bot_id: int,
        display_name: str,
        alias: str,
        prompt: str,
        image_link: str,
    ) -> str:
        while True:
            eop_id = str(randint(0, 999999))
            if not await cls.eop_id_exist(eop_id):
                break

        current_timestamp = int(time() * 1000)
        await cls.create(
            eop_id=eop_id,
            uid=uid,
            diy=diy,
            handle=handle,
            bot_id=bot_id,
            chat_id=0,
            display_name=display_name,
            alias=alias,
            prompt=prompt,
            image_link=image_link,
            create_time=current_timestamp,
            last_talk_time=current_timestamp,
        )
        return eop_id

    # 获取某个用户的所有bot
    @classmethod
    async def get_user_bot(cls, uid: int, eop_id: str | None = None) -> list[dict]:
        data = []
        if eop_id:
            rows = await cls.filter(uid=uid, eop_id=eop_id).values_list(
                "eop_id",
                "alias",
                "display_name",
                "prompt",
                "image_link",
                "create_time",
                "last_talk_time",
                "disable",
            )
        else:
            rows = await cls.filter(uid=uid).values_list(
                "eop_id",
                "alias",
                "display_name",
                "prompt",
                "image_link",
                "create_time",
                "last_talk_time",
                "disable",
            )
        for (
            eop_id,
            alias,
            display_name,
            prompt,
            image_link,
            create_time,
            last_talk_time,
            disable,
        ) in rows:
            data.append(
                {
                    "eop_id": eop_id,
                    "alias": alias,
                    "model": display_name,
                    "prompt": prompt,
                    "image": image_link,
                    "create_time": create_time,
                    "last_talk_time": last_talk_time,
                    "disable": disable,
                }
            )
        return data

    # 删除某个用户相关bot前先删掉相关的会话 todo
    @classmethod
    async def pre_remove_user_bots(
        cls, uid: int
    ) -> list[tuple[str, str, bool, int, int, bool]]:
        return await cls.filter(uid=uid).values_list(
            "eop_id", "handle", "diy", "bot_id", "chat_id", "disable"
        )  # type: ignore

    # 删除某个用户相关bot
    @classmethod
    async def remove_user_bots(cls, uid: int):
        await cls.filter(uid=uid).delete()

    # 判断某个bot是否为该用户且存在
    @classmethod
    async def check_bot_user(cls, eop_id: str, uid: int) -> bool:
        return await cls.filter(eop_id=eop_id, uid=uid).exists()

    # 删除某个bot
    @classmethod
    async def delete_bot(cls, eop_id: str):
        await cls.filter(eop_id=eop_id).delete()

    # 更新某个bot的last_talk_time
    @classmethod
    async def update_bot_last_talk_time(cls, eop_id: str, last_talk_time: int):
        await cls.filter(eop_id=eop_id).update(last_talk_time=last_talk_time)

    # 修改某个bot信息
    @classmethod
    async def modify_bot(
        cls,
        eop_id: str,
        display_name: str | None = None,
        alias: str | None = None,
        prompt: str | None = None,
    ):
        # 拉取旧数据
        rows = await cls.filter(eop_id=eop_id).values_list(
            "display_name", "alias", "prompt"
        )

        display_name = display_name or rows[0][0]
        alias = alias or rows[0][1]
        prompt = prompt or rows[0][2]

        await cls.filter(eop_id=eop_id).update(
            display_name=display_name, alias=alias, prompt=prompt
        )

    # 获取某个bot信息
    @classmethod
    async def pre_modify_bot_info(cls, eop_id: str) -> tuple[str, int, bool]:
        rows = await cls.filter(eop_id=eop_id).values_list("handle", "bot_id", "diy")
        return rows[0][0], rows[0][1], rows[0][2]

    # 获取某个bot的handle、display name、bot id、chat id
    @classmethod
    async def get_bot_data(cls, eop_id: str) -> tuple[str, str, int, int, bool, bool]:
        rows = await cls.filter(eop_id=eop_id).values_list(
            "handle", "display_name", "bot_id", "chat_id", "diy", "disable"
        )
        return rows[0][0], rows[0][1], rows[0][2], rows[0][3], rows[0][4], rows[0][5]

    # 更新某个bot的chat code和chat id
    @classmethod
    async def update_bot_chat_id(cls, eop_id: str, chat_id: int = 0):
        await cls.filter(eop_id=eop_id).update(chat_id=chat_id)

    # 列出所有bot id
    @classmethod
    async def list_all_handle(cls) -> list[str]:
        rows = await cls.filter().values_list("handle")
        data = []
        for handle in rows:
            data.append(handle)
        return data

    # 禁用bot
    @classmethod
    async def disable_bot(cls, eop_id: str):
        await cls.filter(eop_id=eop_id).update(disable=True)
