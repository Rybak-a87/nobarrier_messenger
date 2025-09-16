from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    member_ids: list[int] = Field(..., description="Include yourself too or backend will add you")
    is_group: bool = False


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4096)
