from tortoise import fields
from .db import Model


class History(Model):
    bot_id: string;
    message_id: string;
    create_time: number;
    cursor: string;
    sender: 'human' | 'bot';
    content: string;


    bot_id = fields.TextField(pk=True)
    model = fields.TextField()
    alias = fields.TextField()
    prompot = fields.TextField()
    belong_user = fields.TextField()

    # 创建bot
    @classmethod
    async def create_bot(
        cls, bot_id: str, model: str, alias: str, prompot: str, belong_user: str
    ):
        await cls.create(
            bot_id=bot_id,
            model=model,
            alias=alias,
            prompot=prompot,
            belong_user=belong_user,
        )

    # 删除bot
    @classmethod
    async def remove_bot(cls, bot_id: str):
        await cls.filter(bot_id=bot_id).delete()

    # 删除用户相关bot
    @classmethod
    async def remove_user_bot(cls, belong_user: str):
        await cls.filter(belong_user=belong_user).delete()

    # 修改bot信息
    @classmethod
    async def update_bot(cls, user: str, newPasswd: str):
        await cls.filter(user=user).update(passwd=newPasswd)

    # 获取bot信息
    @classmethod
    async def get_bot_info(cls, bot_id: str) -> tuple[str, str, str, str, str] | None:
        rows = await cls.filter(bot_id=bot_id).values_list(
            "bot_id", "model", "alias", "prompot", "belong_user"
        )
        if rows:
            return rows[0]
        else:
            return None

    # 列出所有bot id
    @classmethod
    async def list_all_bot_id(cls) -> list[str]:
        rows = await cls.filter().values_list("bot_id")
        ll = []
        for bot_id in rows:
            ll.append(bot_id)
        return ll
