from pydantic import BaseModel, Field
from datetime import date


class UpdateSettingBody(BaseModel):
    p_b: str = Field(
        default=None,
        description="p_b值",
    )
    formkey: str = Field(
        default=None,
        description="formkey值",
    )
    proxy: str = Field(
        default=None,
        description="代理地址，支持http和socks",
    )


class AddUserBody(BaseModel):
    user: str = Field(
        description="用户名",
    )
    passwd: str = Field(
        description="密码",
    )
    expire_date: date = Field(
        description="过期日期，格式yyyy-MM-dd",
    )
    admin: bool = Field(description="是否为管理员")


class RenewUserBody(BaseModel):
    expire_date: date = Field(
        description="过期日期，格式yyyy-MM-dd",
    )
