import enum

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nobarrier.database.session import Base


class LanguageEnum(str, enum.Enum):
    RU = "ru"
    EN = "en"


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[LanguageEnum] = mapped_column(
        Enum(LanguageEnum, name="language_enum"), default=LanguageEnum.RU, nullable=False
    )
    chats: Mapped[list["ChatMember"]] = relationship("ChatMember", back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"User ID: {self.id}"