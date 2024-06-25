from pydantic import BaseModel, Field


class UpdateSettingBody(BaseModel):
    p_b: str = Field(
        description="p-b值",
    )
    p_lat: str = Field(
        description="p-lat值",
    )
    formkey: str = Field(
        description="formkey值",
    )
    proxy: str = Field(
        description="http代理地址",
    )


class AddUserBody(BaseModel):
    user: str = Field(
        description="用户名",
    )
    passwd: str = Field(
        description="密码（sha256加密）",
    )
    monthPoints: int = Field(
        description="每月可用积分",
    )
    admin: int = Field(
        description="是否为管理员：1是，0否",
    )
    months: int = Field(
        description="有效期多少个月",
    )


class RenewUserBody(BaseModel):
    user: str = Field(
        description="用户名",
    )
    remainPoints: int = Field(
        description="当前剩余积分",
    )
    monthPoints: int = Field(
        description="每月可用积分",
    )
    admin: int = Field(
        description="用户级别，0是管理员，1是普通用户，2是高级用户",
    )
    addMonths: int = Field(
        description="有效期增加多少个月，0就是不变",
    )


class HashUploadBody(BaseModel):
    uploadKey: str = Field(
        description="上传密钥",
    )
    queryHash: dict = Field(
        description="query hash",
    )
    subHash: dict = Field(
        description="sub_hash hash",
    )
