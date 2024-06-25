from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    user: str = Field(
        description="登陆用户名",
    )
    passwd: str = Field(
        description="登陆密码",
    )


class UpdatePasswdBody(BaseModel):
    oldPasswd: str = Field(
        description="加密的旧密码",
    )
    newPasswd: str = Field(
        description="加密的新密码",
    )


class ChatTitleBody(BaseModel):
    title: str = Field(
        description="名称",
    )


class CreateBotBody(BaseModel):
    botName: str = Field(
        description="bot名称",
    )
    baseBotId: int = Field(
        description="基础机器人id",
    )
    baseBotModel: str = Field(
        description="基础机器人model",
    )
    description: str = Field(
        description="描述",
    )
    prompt: str = Field(
        description="预设内容",
    )
    citeSource: bool = Field(
        description="是否引用资源",
    )
    sourceIds: list[int] = Field(
        default=[],
        description="引用资源id，可以空着",
    )


class AnswerAgain(BaseModel):
    messageId: int = Field(
        description="要重新回答的消息id",
    )
    price: int = Field(
        description="消耗积分",
    )


class AnswerStop(BaseModel):
    messageId: int = Field(
        description="要停止回答的消息id",
    )


class EditBotBody(BaseModel):
    botName: str = Field(
        description="botName，如果不修改发原名称就行",
    )
    botId: int = Field(
        description="botId",
    )
    botHandle: str = Field(
        description="botHandle",
    )
    baseBotId: int = Field(
        description="baseBotId",
    )
    baseBotModel: str = Field(
        description="baseBotModel",
    )
    description: str = Field(
        description="description",
    )
    prompt: str = Field(
        description="prompt",
    )
    citeSource: bool = Field(
        description="是否引用资源",
    )
    addSourceIds: list[int] = Field(
        default=[],
        description="要添加的资源id",
    )
    removeSourceIds: list[int] = Field(
        default=[],
        description="要删除的资源id",
    )


class EditSourceBody(BaseModel):
    sourceId: int = Field(
        description="资源id",
    )
    title: str = Field(
        description="标题",
    )
    content: str = Field(
        description="内容",
    )
