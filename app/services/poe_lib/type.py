from pydantic import BaseModel


class Text(BaseModel):
    """文本信息"""

    content: str


class MsgId(BaseModel):
    """消息id"""

    question_msg_id: int
    question_create_time: int
    answer_msg_id: int
    answer_create_time: int


class End(BaseModel):
    """回答完毕"""

    pass


class NewChat(BaseModel):
    """新会话"""

    chat_id: int


class TalkError(BaseModel):
    """错误"""

    content: str


class SessionDeleted(BaseModel):
    """会话被删除"""

    pass


class ReachedLimit(BaseModel):
    """次数上限"""

    pass


class ModelInfo(BaseModel):
    """模型信息"""

    model: str
    description: str
    diy: bool
    limited: bool
    bot_id: int


class UserInfo(BaseModel):
    """账号信息"""

    email: str = ""
    subscription_actived: bool = False
    plan_type: str = ""
    expire_time: str = ""


class ServerError(Exception):
    """请求报错 server error"""

    pass
