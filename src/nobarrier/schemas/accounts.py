import datetime
import re

from pydantic import BaseModel, Field, validator


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class UserRead(UserBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class UserCheck(BaseModel):
    id: int

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str = Field(
        min_length=3,
        max_length=128,
        # regex=r'^(?=.*[!@#$%^&*()]).+$',
        description="Password must be strong"
    )

    # @validator('password')
    # def password_complexity(cls, value):
    #     checks = {
    #         "uppercase letter": r"[A-Z]",
    #         "lowercase letter": r"[a-z]",
    #         "digit": r"\d",
    #         "special character": r"[!@#$%^&*(),.?\":{}|<>]"
    #     }
    #     for name, pattern in checks.items():
    #         if not re.search(pattern, value):
    #             raise ValueError(f"Password must contain at least one {name}")
    #     return value
