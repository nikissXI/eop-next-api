from pydantic import BaseModel, Field


class CreateBody(BaseModel):
    model: str = Field(
        description="模型，无次数限制模型：ChatGPT、Claude； 有次数限制模型：ChatGPT4、Claude-2-100k",
    )
    prompt: str = Field(
        default="You are a large language model. Follow the user's instructions carefully.",
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
    alias: str = Field(
        description="会话名",
    )
    model: str = Field(
        description="模型，无次数限制模型：ChatGPT、Claude； 有次数限制模型：ChatGPT4、Claude-2-100k",
    )
    prompt: str = Field(
        description="预设内容",
    )
