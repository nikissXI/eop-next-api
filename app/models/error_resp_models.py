from pydantic import BaseModel, Field


class Response422(BaseModel):
    code: int = Field(
        title="错误代码",
    )
    msg: str = Field(
        title="错误信息",
    )
