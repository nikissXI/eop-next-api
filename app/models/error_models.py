from pydantic import BaseModel, Field


class Response422(BaseModel):
    code: int = Field(
        description="错误代码",
    )
    msg: str = Field(
        description="错误信息",
    )
