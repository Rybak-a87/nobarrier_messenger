from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nobarrier.database.models import Chat, ChatMember, Message
# from nobarrier.services.websockets import WebSocketService


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(self, user_id: int, member_ids: list[int], is_group: bool) -> dict:
        members = set(member_ids) | {user_id}
        chat = Chat(is_group=is_group)
        self.session.add(chat)
        await self.session.flush()
        for user_id in members:
            self.session.add(ChatMember(chat_id=chat.id, user_id=user_id))
        await self.session.commit()
        # await WebSocketService(self.session).notify_new_chat(chat)
        return {"chat_id": chat.id, "is_group": chat.is_group, "member_ids": list(members)}
    
    async def get_chats(self, user_id: int) -> list[dict]:
        # chats_query = (
        #     select(
        #         Chat.id,
        #         Chat.is_group,
        #         func.array_agg(ChatMember.user_id),
        #         # func.array_agg(ChatMember.user_id).label("member_ids"),
        #     )
        #     .join(ChatMember, ChatMember.chat_id == Chat.id)
        #     .where(ChatMember.user_id == user_id)
        #     .group_by(Chat.id)
        #     .order_by(Chat.id)
        # )
        # chats = (await self.session.execute(chats_query)).all()
        # return [
        #     {"chat_id": chat.id, "is_group": chat.is_group, "member_ids": [int(i) for i in chat.array_agg]}
        #     for chat in chats
        # ]
        chats_query = (
            select(Chat)
            .join(ChatMember)
            .where(ChatMember.user_id == user_id)
            .options(selectinload(Chat.members))
            .order_by(Chat.id)
        )

        result = await self.session.execute(chats_query)
        chats = result.scalars().unique().all()
        return [
            {
                "chat_id": chat.id,
                "is_group": chat.is_group,
                "member_ids": [int(chat_member.user_id) for chat_member in chat.members],
            }
            for chat in chats
        ]
        
    async def get_messages(self, user_id: int, chat_id: int, limit: int, offset: int) -> list[dict]:
        # verify membership
        member = await self.session.scalar(
            select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
        )
        if not member:
            raise HTTPException(403, detail="Not a member of this chat")

        messages_query = (
            select(Message.id, Message.sender_id, Message.content, Message.created_at)
            .where(Message.chat_id == chat_id)
            .order_by(Message.id.desc())
            .limit(limit)
            .offset(offset)
        )
        messages = (await self.session.execute(messages_query)).all()
        return [
            {
                "id": message.id,
                "chat_id": chat_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in reversed(messages)
        ]

    async def send_message(self, chat_id: int, user_id: int, content: str):
        chat = await self.session.get(Chat, chat_id)
        if not chat:
            raise ValueError(f"Chat {chat_id} does not exist")
        message = Message(
            chat_id=chat_id,
            sender_id=user_id,
            content=content,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "content": message.content
        }
