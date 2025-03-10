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
    mimeType: str = Field(
        title="mimeType",
        examples=["image/png", "text/javascript"],
    )
    width: int | None = Field(
        title="width",
        examples=[None, 1024],
    )
    height: int | None = Field(
        title="height",
        examples=[None, 1024],
    )
    size: int = Field(
        title="文件大小",
        examples=[1652645],
    )


class BotMessageAdd(BaseModel):
    """回答的内容"""

    state: str = Field(
        title="回答状态",
        examples=["incomplete", "complete", "cancelled"],
    )
    messageStateText: str | None = Field(
        title="异常状态文本",
        examples=[
            "信息或附件过大。请缩短信息或上传较小的附件，或考虑使用其他支持更大信息的机器人。"
        ],
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


class PriceCost(BaseModel):
    """花费信息"""

    price: int = Field(
        title="消耗点数",
    )


class PriceCache(BaseModel):
    """花费缓存"""

    standardPrice: int = Field(
        title="标准消息消耗",
    )
    displayPrice: int = Field(
        title="显示消耗",
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


class NeedDeleteChat(Exception):
    """会话已被删除"""

    pass
