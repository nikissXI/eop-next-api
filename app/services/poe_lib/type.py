from pydantic import BaseModel


class Text(BaseModel):
    """文本信息"""

    content: str


class MsgId(BaseModel):
    """消息id"""

    question_msg_id: int
    answer_msg_id: int


class End(BaseModel):
    """回答完毕"""

    pass


class NewChat(BaseModel):
    """新会话"""

    chat_code: str
    chat_id: int


class TalkError(BaseModel):
    """错误"""

    content: str
