from pydantic import BaseModel, Field


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


class PageInfo(BaseModel):
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
    pageInfo: PageInfo = Field(
        title="翻页信息",
    )


class SearchBotsRespBody(BaseModel):
    bots: list[Bot] = Field(
        title="bot列表",
    )
    pageInfo: PageInfo = Field(
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
