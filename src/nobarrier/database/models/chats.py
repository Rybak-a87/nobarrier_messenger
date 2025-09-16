from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, Boolean, ForeignKey

from nobarrier.database.session import Base


class Chat(Base):
    __tablename__ = "chats"

    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    members: Mapped[list["ChatMember"]] = relationship(back_populates="chat")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat")

    def __repr__(self):
        return f"Chat ID: {self.id}"


class ChatMember(Base):
    __tablename__ = "chat_members"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chat: Mapped[Chat] = relationship(back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="chats")

    def __repr__(self):
        return f"Chat Member ID: {self.id}"


class Message(Base):
    __tablename__ = "messages"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    content: Mapped[str] = mapped_column(Text())
    chat: Mapped[Chat] = relationship(back_populates="messages")

    def __repr__(self):
        return f"Message ID: {self.id}"
