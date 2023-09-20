from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    user: str = Field(
        description="登陆用户名",
    )
    passwd: str = Field(
        description="登陆密码",
    )


class LoginResp(BaseModel):
    code: int = 0
    access_token: str = "eyJhbxxxxxxxxxxxxxxxxxxxxxxxx"
    token_type: str = "Bearer"


class UpdatePasswdBody(BaseModel):
    old_passwd: str = Field(
        description="旧密码",
    )
    new_passwd: str = Field(
        description="新密码",
    )
