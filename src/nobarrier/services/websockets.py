import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from nobarrier.core.security import SecurityService
from nobarrier.core.websockets import WSConnectionManager
from nobarrier.database.models.chats import Message, ChatMember, Chat

ws_manager = WSConnectionManager()


class WebSocketService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    async def authenticate_ws(token: str):
        return SecurityService().get_current_user(token)

    async def handle_message(self, user_id: int, chat_id: int, data: dict):
        content = (data.get("content") or "").strip()
        if not content:
            return

        message = Message(chat_id=chat_id, sender_id=user_id, content=content)
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

        member_ids = await self.session.scalars(
            select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
        )
        member_ids = list(member_ids)

        payload = {
            "type": "message",
            "chat_id": chat_id,
            "sender_id": user_id,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
        await ws_manager.broadcast_to_users(member_ids, payload)

    async def notify_new_chat(self, chat: Chat):
        member_ids = await self.session.scalars(
            select(ChatMember.user_id).where(ChatMember.chat_id == chat.id)
        )
        member_ids = list(member_ids)

        payload = {
            "type": "new_chat",
            "chat_id": chat.id,
            "is_group": chat.is_group,
            "member_ids": member_ids,
        }

        await ws_manager.broadcast_to_users(member_ids, payload)

    async def web_socket_user(self, web_socket: WebSocket, chat_id: int):
        token = web_socket.query_params.get("token")
        if not token:
            await web_socket.close(code=4401)
            return
        user = await self.authenticate_ws(token)
        try:
            await ws_manager.connect(user.id, web_socket)
            while True:
                data = await web_socket.receive_json()
                mtype = data.get("type")
                if mtype == "ping":
                    await web_socket.send_json({
                        "type": "pong",
                        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    })
                    continue
                if mtype == "message":
                    await self.handle_message(user.id, chat_id, data)
                    continue

        except WebSocketDisconnect:
            pass
        finally:
            await ws_manager.disconnect(user.id, web_socket)

    # async def web_socket_chat(self, web_socket: WebSocket, chat_id: int) -> None:
    #     token = web_socket.query_params.get("token")
    #
    #     if not token:
    #         await web_socket.close(code=4401)
    #         return
    #     try:
    #         user = await self.authenticate_ws(token)
    #         chat_member = await self.session.scalar(
    #             select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user.id)
    #         )
    #         if not chat_member:
    #             await web_socket.close(code=4403)
    #             return
    #
    #         await ws_manager.connect(chat_id, web_socket)
    #         while True:
    #             data = await web_socket.receive_json()
    #             mtype = data.get("type")
    #             if mtype == "ping":
    #                 await web_socket.send_json({"type": "pong", "ts": datetime.datetime.utcnow().isoformat()})
    #                 continue
    #             if mtype != "message":
    #                 await web_socket.send_json({"type": "error", "error": "unknown_type"})
    #                 continue
    #
    #             content = (data.get("content") or "").strip()
    #             if not content:
    #                 await web_socket.send_json({"type": "error", "error": "empty_content"})
    #                 continue
    #
    #             msg = Message(chat_id=chat_id, sender_id=user.id, content=content)
    #             self.session.add(msg)
    #             await self.session.commit()
    #             await self.session.refresh(msg)
    #
    #             payload = {
    #                 "type": "message",
    #                 "id": msg.id,
    #                 "chat_id": chat_id,
    #                 "sender_id": user.id,
    #                 "content": msg.content,
    #                 "created_at": msg.created_at.isoformat(),
    #             }
    #             await ws_manager.broadcast(chat_id, payload)
    #
    #     except WebSocketDisconnect:
    #         pass
    #     finally:
    #         await ws_manager.disconnect(chat_id, web_socket)
