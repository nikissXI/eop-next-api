from pydantic import BaseModel, Field


class LoginReqBody(BaseModel):
    user: str = Field(
        title="登陆用户名",
    )
    passwd: str = Field(
        title="登陆密码",
    )


class UpdatePasswdReqBody(BaseModel):
    oldPasswd: str = Field(
        title="加密的旧密码",
    )
    newPasswd: str = Field(
        title="加密的新密码",
    )


class ChatTitleReqBody(BaseModel):
    title: str = Field(
        title="名称",
    )


class CreateBotReqBody(BaseModel):
    botName: str = Field(
        title="bot名称",
    )
    baseBotId: int = Field(
        title="基础机器人id",
    )
    baseBotModel: str = Field(
        title="基础机器人model",
    )
    description: str = Field(
        title="描述",
    )
    prompt: str = Field(
        title="预设内容",
    )
    citeSource: bool = Field(
        title="是否引用资源",
    )
    sourceIds: list[int] = Field(
        default=[],
        title="引用资源id，可以空着",
    )


class AnswerReqAgain(BaseModel):
    messageId: int = Field(
        title="要重新回答的消息id",
    )
    price: int = Field(
        title="消耗积分",
    )


class AnswerReqStop(BaseModel):
    messageId: int = Field(
        title="要停止回答的消息id",
    )


class EditBotReqBody(BaseModel):
    botName: str = Field(
        title="botName，如果不修改发原名称就行",
    )
    botId: int = Field(
        title="botId",
    )
    botHandle: str = Field(
        title="botHandle",
    )
    baseBotId: int = Field(
        title="baseBotId",
    )
    baseBotModel: str = Field(
        title="baseBotModel",
    )
    description: str = Field(
        title="描述",
    )
    prompt: str = Field(
        title="prompt",
    )
    citeSource: bool = Field(
        title="是否引用资源",
    )
    addSourceIds: list[int] = Field(
        default=[],
        title="要添加的资源id",
    )
    removeSourceIds: list[int] = Field(
        default=[],
        title="要删除的资源id",
    )


class EditSourceReqBody(BaseModel):
    sourceId: int = Field(
        title="资源id",
    )
    title: str = Field(
        title="标题",
    )
    content: str = Field(
        title="内容",
    )
