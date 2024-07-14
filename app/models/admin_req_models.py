from pydantic import BaseModel, Field


class UpdateSettingReqBody(BaseModel):
    p_b: str = Field(
        title="p-b值",
    )
    p_lat: str = Field(
        title="p-lat值",
    )
    formkey: str = Field(
        title="formkey值",
    )
    proxy: str = Field(
        title="http代理地址",
    )


class AddUserReqBody(BaseModel):
    user: str = Field(
        title="用户名",
    )
    passwd: str = Field(
        title="密码（sha256加密）",
    )
    monthPoints: int = Field(
        title="每月可用积分",
    )
    admin: int = Field(
        title="是否为管理员：1是，0否",
    )
    months: int = Field(
        title="有效期多少个月",
    )


class RenewUserReqBody(BaseModel):
    user: str = Field(
        title="用户名",
    )
    remainPoints: int = Field(
        title="当前剩余积分",
    )
    monthPoints: int = Field(
        title="每月可用积分",
    )
    admin: int = Field(
        title="是否为管理员：1是，0否",
    )
    addMonths: int = Field(
        title="有效期增加多少个月，0就是不变",
    )


class HashUploadReqBody(BaseModel):
    uploadKey: str = Field(
        title="上传密钥",
    )
    queryHash: dict = Field(
        title="query hash",
    )
    subHash: dict = Field(
        title="sub_hash hash",
    )
