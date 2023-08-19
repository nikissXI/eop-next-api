from pydantic import BaseModel, Field


class Response422(BaseModel):
    code: int = Field(1234, description="错误代码")
    msg: str = Field("error message", description="错误信息")
