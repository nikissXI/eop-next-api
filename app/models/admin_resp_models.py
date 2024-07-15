from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class BasicRespBody(BaseModel, Generic[DataT]):
    code: int = Field(
        default=0,
        title="业务状态码，0是正常",
        examples=[0],
    )
    msg: str = Field(
        default="success",
        title="响应信息，如果出错，错误信息在这里",
        examples=["success"],
    )
    data: DataT | None = Field(
        default=None,
        title="响应数据",
    )


class UserInfoRespBody(BaseModel):
    user: str = Field(
        title="用户名",
        examples=["nikiss"],
    )
    remainPoints: int = Field(
        title="剩余积分",
        examples=[1000],
    )
    monthPoints: int = Field(
        title="每月积分",
        examples=[2000],
    )
    isAdmin: int = Field(
        title="是否为管理员",
        examples=[0, 1],
    )
    resetDate: int = Field(
        title="重置积分时间",
        examples=[1693230928703],
    )
    expireDate: int = Field(
        title="授权过期时间",
        examples=[1693230928703],
    )


class NewPasswdRespBody(BaseModel):
    passwd: str = Field(
        title="新密码",
        examples=["abcdefg"],
    )


class ConfigRespBody(BaseModel):
    p_b: str = Field(
        title="p-b值",
        examples=["3YPe_Ub3EJDAZW5oHnCcNA%3D%3D"],
    )
    p_lat: str = Field(
        title="p-lat值",
        examples=["EzAa%2BFOhAV1qY07LVgdY7P11FkiFdZLzJaTCYEZ4ZQ%3D%3D"],
    )
    formkey: str = Field(
        title="formkey值",
        examples=["4d926adfb34ac9dc1942c1d9f20217b3"],
    )
    proxy: str = Field(
        title="代理地址",
        examples=["http://127.0.0.1:7890"],
    )


class AccountRespBody(BaseModel):
    email: str = Field(
        title="email",
        examples=["xxx@gmail.com"],
    )
    subscriptionActivated: bool = Field(
        title="是否购买订阅",
        examples=[True, False],
    )
    planType: str | None = Field(
        title="订阅计划，没订阅的话该值为None",
        examples=["monthly", "yearly"],
    )
    expireTime: int | None = Field(
        title="订阅到期时间，没订阅的话该值为None",
        examples=[1693230928703],
    )
    remainPoints: int = Field(
        title="账号积分余额",
        examples=[9999],
    )
    monthPoints: int = Field(
        title="账号每月积分",
        examples=[100000],
    )
    pointsResetTime: int = Field(
        title="积分重置时间",
        examples=[1693230928703],
    )
