from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from services.poe_lib.type import (
    BotMessageAdded,
    BotMessageCreated,
    ChatTitleUpdated,
    TalkError,
)

DataT = TypeVar("DataT")


class BasicRespBody(BaseModel, Generic[DataT]):
    code: int = Field(
        default=0,
        title="业务状态码，0是正常",
        examples=[0],
    )
    msg: str = Field(
        default="success",
        title="响应信息，如果出错，错误信息在这里",
        examples=["success"],
    )
    data: DataT | None = Field(
        default=None,
        title="响应数据",
    )


class LoginRespBody(BaseModel):
    accessToken: str = Field(
        title="token值",
        examples=["eyJhbxxxxxxxxxxxxxxxxxxxxx"],
    )
    tokenType: str = Field(
        title="token类型",
        examples=["Bearer"],
    )


class UserInfoRespBody(BaseModel):
    user: str = Field(
        title="用户名",
        examples=["nikiss"],
    )
    remainPoints: int = Field(
        title="剩余积分",
        examples=[1000],
    )
    monthPoints: int = Field(
        title="每月积分",
        examples=[2000],
    )
    isAdmin: int = Field(
        title="是否为管理员",
        examples=[0, 1],
    )
    resetDate: int = Field(
        title="重置积分时间",
        examples=[1693230928703],
    )
    expireDate: int = Field(
        title="授权过期时间",
        examples=[1693230928703],
    )


class Category(BaseModel):
    categoryName: str = Field(
        title="类别名",
        examples=["Official", "Popular"],
    )
    translatedCategoryName: str = Field(
        title="译名",
        examples=["官方", "流行"],
    )


class Bot(BaseModel):
    model: str = Field(
        title="bot名称",
        examples=["ChatGPT", "iKun"],
    )
    imgUrl: str = Field(
        title="bot头像链接",
        examples=["https://xxx/bot.jpg"],
    )
    description: str = Field(
        title="描述",
        examples=["由gpt-3.5-turbo驱动。", "练习时长两年半"],
    )
    botType: str = Field(
        title="bot类型",
        examples=["官方", "第三方", "自定义"],
    )
    monthlyActive: int = Field(
        title="每月使用用户",
        examples=[0, 111],
    )


class BotListPageInfo(BaseModel):
    endCursor: str = Field(
        title="翻页游标",
        examples=["1017"],
    )
    hasNextPage: bool = Field(
        title="是否有下一页",
        examples=[True, False],
    )


class ExploreBotsRespBody(BaseModel):
    categoryList: list[Category] = Field(
        title="类别列表，只有cursor为0的时候才返回",
    )
    bots: list[Bot] = Field(
        title="bot列表",
    )
    pageInfo: BotListPageInfo = Field(
        title="翻页信息",
    )


class SearchBotsRespBody(BaseModel):
    bots: list[Bot] = Field(
        title="bot列表",
    )
    pageInfo: BotListPageInfo = Field(
        title="翻页信息",
    )


class UserBotRespBody(BaseModel):
    name: str = Field(
        title="bot名称",
        examples=["ChatGPT", "iKun"],
    )
    imgUrl: str = Field(
        title="bot头像链接",
        examples=["https://xxx/bot.jpg"],
    )
    botType: str = Field(
        title="bot类型",
        examples=["官方", "第三方", "自定义"],
    )


class BasicBotRespBody(BaseModel):
    botName: str = Field(
        title="bot名称",
        examples=["ChatGPT", "DALL-E-3"],
    )
    imgUrl: str = Field(
        title="bot头像链接",
        examples=["https://xxx/bot.jpg"],
    )
    botId: int = Field(
        title="bot id",
        examples=[3004, 2828029],
    )
    model: str = Field(
        title="模型名称",
        examples=["chinchilla", "dalle3"],
    )
    isImageGen: bool = Field(
        title="是否为图像生成模型",
        examples=[True, False],
    )


class UploadSourceRespBody(BaseModel):
    sourceId: int = Field(
        title="资源id",
        examples=[2380421],
    )
    sourceTitle: str = Field(
        title="资源文件名或标题",
        examples=["xxx.txt", "yyy.docx"],
    )


class GetTextSourceRespBody(BaseModel):
    title: str = Field(
        title="标题",
        examples=["txt title"],
    )
    content: str = Field(
        title="文本内容",
        examples=["this is text content"],
    )


class SourceBody(BaseModel):
    sourceId: int = Field(
        title="资源id",
        examples=[2413096],
    )
    sourceType: str = Field(
        title="资源类型",
        examples=["text", "file"],
    )
    title: str = Field(
        title="资源名称",
        examples=["xxx.txt", "yyy.docx"],
    )
    lastUpdatedTime: int = Field(
        title="更新时间",
        examples=[1717739865091089],
    )


class CustomBotInfo(BaseModel):
    botName: str = Field(
        title="bot名称",
        examples=["CatBot"],
    )
    botId: int = Field(
        title="bot id",
        examples=[4368380],
    )
    botHandle: str = Field(
        title="bot handle",
        examples=["1Fp4BqjkQKpmiSj5Taey"],
    )
    baseBotId: int = Field(
        title="基础bot id",
        examples=[3004],
    )
    baseBotModel: str = Field(
        title="基础bot模型",
        examples=["chinchilla"],
    )
    description: str = Field(
        title="bot描述",
        examples=["这是机器人的简介"],
    )
    prompt: str = Field(
        title="prompt",
        examples=["这是机器人的prompt内容"],
    )
    citeSource: bool = Field(
        title="是否引用自定义资源",
        examples=[True, False],
    )
    sourceList: list[SourceBody] = Field(
        title="资源列表",
    )


class GetEditBotRespBody(BaseModel):
    basicBotList: list[BasicBotRespBody] = Field(
        title="自定义bot可使用的基础bot列表",
    )
    botInfo: CustomBotInfo = Field(
        title="bot信息",
    )


class GetBotInfoRespBody(BaseModel):
    botName: str = Field(
        title="bot名称",
        examples=["ChatGPT"],
    )
    botId: int = Field(
        title="bot id",
        examples=[3004],
    )
    botHandle: str = Field(
        title="bot handle",
        examples=["chinchilla"],
    )
    description: str = Field(
        title="bot描述",
        examples=["这个是GPT3.5"],
    )
    allowImage: bool = Field(
        title="是否允许发送图片",
        examples=[True, False],
    )
    allowFile: bool = Field(
        title="是否允许发送文件",
        examples=[True, False],
    )
    uploadFileSizeLimit: int = Field(
        title="上传的附件大小上限（50MB）",
        examples=[50000000],
    )
    imgUrl: str = Field(
        title="bot头像链接",
        examples=["https://xxx/bot.jpg"],
    )
    price: int = Field(
        title="对话消耗积分",
        examples=[20],
    )
    remainTalkTimes: int = Field(
        title="剩余积分还可以对话多少次",
        examples=[66],
    )
    botType: str = Field(
        title="bot类型",
        examples=["官方", "第三方", "自定义"],
    )
    added: bool = Field(
        title="用户是否添加到我的bot",
        examples=[True, False],
    )
    canAccess: bool = Field(
        title="该bot是否可用",
        examples=[True, False],
    )


class ChatRespBody(BaseModel):
    chatCode: str = Field(
        title="会话code",
        examples=["abc23kjkwei"],
    )
    title: str = Field(
        title="会话名称",
        examples=["会话1"],
    )
    bot: str = Field(
        title="bot名称",
        examples=["ChatGPT"],
    )
    imgUrl: str = Field(
        title="bot头像链接",
        examples=["https://xxx/bot.jpg"],
    )
    lastTalkTime: int = Field(
        title="最后一次对话时间",
        examples=[1719676800000],
    )
    disable: bool = Field(
        title="会话是否禁用",
        examples=[True, False],
    )


class BotInfo(BaseModel):
    botName: str = Field(
        title="bot名称",
        examples=["CatBot"],
    )
    botId: int = Field(
        title="bot id",
        examples=[4368380],
    )
    botHandle: str = Field(
        title="bot handle",
        examples=["chinchilla"],
    )
    description: str = Field(
        title="bot描述",
        examples=["这个是GPT3.5"],
    )
    allowImage: bool = Field(
        title="是否允许发送图片",
        examples=[True, False],
    )
    allowFile: bool = Field(
        title="是否允许发送文件",
        examples=[True, False],
    )
    uploadFileSizeLimit: int = Field(
        title="上传的附件大小上限（50MB）",
        examples=[50000000],
    )
    imgUrl: str = Field(
        title="bot头像链接",
        examples=["https://xxx/bot.jpg"],
    )
    price: int = Field(
        title="对话消耗积分",
        examples=[20],
    )
    botType: str = Field(
        title="bot类型",
        examples=["官方", "第三方", "自定义"],
    )
    canAccess: bool = Field(
        title="该bot是否可用",
        examples=[True, False],
    )


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


class MessageNodeRespBody(BaseModel):
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
        examples=["啊？"],
    )
    attachments: list[Attachments] = Field(
        title="附件列表",
    )
    author: str = Field(
        title="作者",
        examples=["human", "bot", "chat_break"],
    )


class ChatPageInfo(BaseModel):
    hasPreviousPage: bool = Field(
        title="是否前一页",
        examples=[True, False],
    )
    startCursor: str = Field(
        title="翻页游标",
        examples=["2692997857"],
    )


class ChatInfoRespBody(BaseModel):
    botInfo: BotInfo = Field(
        title="bot信息",
    )
    historyNodes: list[MessageNodeRespBody] = Field(
        title="消息列表",
    )
    pageInfo: ChatPageInfo = Field(
        title="翻页信息",
    )


class NewChat(BaseModel):
    chatCode: str = Field(
        title="类别列表，只有cursor为0的时候才返回",
    )
    botInfo: BotInfo = Field(
        title="bot信息",
    )


class TalkRespBody(BaseModel):
    data_type: str = Field(
        title="数据类型",
        examples=[
            "newChat",
            "humanMessageCreated",
            "botMessageCreated",
            "botMessageAdded",
            "chatTitleUpdated",
            "talkError",
        ],
    )
    data_content: (
        NewChat | MessageNodeRespBody | BotMessageAdded | ChatTitleUpdated | TalkError
    ) = Field(
        title="数据内容",
    )
