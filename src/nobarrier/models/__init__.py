from pydantic import BaseModel


class BaseClassModel(BaseModel):
    id: int

    class Config:
        orm_mode = True
    