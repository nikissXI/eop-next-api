from pydantic import BaseModel, Field


class HumanMessageCreated(BaseModel):
    """新消息数据"""

    messageId: int
    creationTime: int


class Attachments(BaseModel):
    name: str = Field(
        title="附件名",
        examples=["tmp.txt"],
    )
    url: str = Field(
        title="下载链接",
        examples=[
            "https://pfst.cf2.poecdn.net/base/text/0723b69e0a0c72fdb2885f3c072c0706169f07c8b2bff3d57552e40a92e89d14?pmaid=113715453"
        ],
    )


class BotMessageAdd(BaseModel):
    """回答的内容"""

    state: str = Field(
        title="回答状态",
        examples=["incomplete", "complete", "cancelled"],
    )
    messageId: int = Field(
        title="消息id",
        examples=[2692997857],
    )
    creationTime: int = Field(
        title="创建时间",
        examples=[1692964266475260],
    )
    text: str = Field(
        title="消息内容",
        examples=["这是回答内容"],
    )
    attachments: list[Attachments] = Field(
        title="附件列表",
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


class UnsupportedFileType(Exception):
    """文件类型不支持"""

    pass


class FileTooLarge(Exception):
    """文件过大"""

    pass


class RefetchChannel(Exception):
    """重新连接WS"""

    pass
