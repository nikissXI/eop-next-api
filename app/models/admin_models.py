from pydantic import BaseModel, Field


class UpdateSettingBody(BaseModel):
    p_b: str | None = Field(
        default=None,
        description="p-b值",
    )
    p_lat: str | None = Field(
        default=None,
        description="p-lat值",
    )
    formkey: str | None = Field(
        default=None,
        description="formkey值",
    )
    proxy: str | None = Field(
        default=None,
        description="代理地址，支持http和socks",
    )
    telegram_url: str | None = Field(
        default=None,
        description="telegram群链接",
    )
    discord_url: str | None = Field(
        default=None,
        description="discord群链接",
    )
    weixin_url: str | None = Field(
        default=None,
        description="微信群链接",
    )
    qq_url: str | None = Field(
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


class HashUploadBody(BaseModel):
    upload_key: str = Field(
        description="上传密钥",
    )
    query_hash: dict = Field(
        description="query hash",
    )
    sub_hash: dict = Field(
        description="sub_hash hash",
    )
