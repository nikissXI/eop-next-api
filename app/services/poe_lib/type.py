from pydantic import BaseModel, Field


class BotMessageCreated(BaseModel):
    """新消息数据"""

    messageId: int
    creationTime: int


class BotMessageAdded(BaseModel):
    """回答的内容"""

    state: str = Field(
        title="回答状态",
        examples=["incomplete", "complete", "cancelled"],
    )
    text: str = Field(
        title="回答的内容",
    )


class ChatTitleUpdated(BaseModel):
    """新会话标题更新"""

    title: str = Field(
        title="会话标题",
    )


class TalkError(BaseModel):
    """错误"""

    errMsg: str


class ServerError(Exception):
    """请求报错 server error"""

    pass


class RefetchChannel(Exception):
    """重新连接WS"""

    pass
