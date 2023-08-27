from pydantic import BaseModel, Field


class CreateBody(BaseModel):
    model: str = Field(
        description="模型名称",
    )
    prompt: str = Field(
        default="",
        description="预设内容",
    )
    alias: str = Field(
        default="新会话",
        description="会话名",
    )


class TalkBody(BaseModel):
    q: str = Field(
        description="问题内容",
    )


class ModifyBotBody(BaseModel):
    alias: str | None = Field(
        default=None,
        description="会话名",
    )
    model: str | None = Field(
        default=None,
        description="模型名称",
    )
    prompt: str | None = Field(
        default=None,
        description="预设内容",
    )
