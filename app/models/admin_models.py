from pydantic import BaseModel, Field


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
    telegram_url: str = Field(
        default=None,
        description="telegram群链接",
    )
    discord_url: str = Field(
        default=None,
        description="discord群链接",
    )
    weixin_url: str = Field(
        default=None,
        description="微信群链接",
    )
    qq_url: str = Field(
        default=None,
        description="QQ群链接",
    )


class AddUserBody(BaseModel):
    user: str = Field(
        description="用户名",
    )
    passwd: str = Field(
        description="密码",
    )
    level: int = Field(
        description="用户等级：0是管理员，1是普通用户，2是高级用户",
    )
    expire_date: int = Field(
        description="过期日期，格式13位整数时间戳，如果创建的是管理员该字段无效",
    )


class RenewUserBody(BaseModel):
    level: int = Field(
        description="用户级别，0是管理员，1是普通用户，2是高级用户",
    )
    expire_date: int = Field(
        description="过期日期，格式13位整数时间戳",
    )
