from typing import Optional
from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    user: str = Field(description="登陆用户名")
    passwd: str = Field(description="登陆密码")


class Resp(BaseModel):
    code: int = 0


class LoginResp(Resp):
    access_token: str = "eyJhbxxxxxxxxxxxxxxxxxxxxxxxx"
    token_type: str = "Bearer"


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
    alias: Optional[str] = Field(
        description="会话名",
    )
    model: Optional[str] = Field(
        description="模型，无次数限制模型：ChatGPT、Claude； 有次数限制模型：ChatGPT4、Claude-2-100k",
    )
    prompt: Optional[str] = Field(
        description="预设内容",
    )


class UpdatePasswdBody(BaseModel):
    old_passwd: str = Field(
        description="旧密码",
    )
    new_passwd: str = Field(
        description="新密码",
    )
