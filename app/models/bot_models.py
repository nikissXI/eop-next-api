from pydantic import BaseModel, Field


class CreateBody(BaseModel):
    model: str = Field(
        description="模型名称",
    )
    prompt: str = Field(
        description="预设内容",
    )
    alias: str = Field(
        description="会话名",
    )


class TalkBody(BaseModel):
    q: str = Field(
        description="问题内容",
    )


class ModifyBotBody(BaseModel):
    alias: str = Field(
        description="会话名",
    )
    model: str = Field(
        description="模型名称",
    )
    prompt: str = Field(
        description="预设内容",
    )
