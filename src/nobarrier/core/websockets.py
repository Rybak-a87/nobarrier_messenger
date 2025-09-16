import asyncio
import json

from fastapi import WebSocket


# class WSConnectionManager:
#     def __init__(self) -> None:
#         self.rooms: dict[int, set[WebSocket]] = {}
#         self.lock = asyncio.Lock()
#
#     async def connect(self, chat_id: int, ws: WebSocket) -> None:
#         await ws.accept()
#         async with self.lock:
#             self.rooms.setdefault(chat_id, set()).add(ws)
#
#     async def disconnect(self, chat_id: int, ws: WebSocket) -> None:
#         async with self.lock:
#             if chat_id in self.rooms and ws in self.rooms[chat_id]:
#                 self.rooms[chat_id].remove(ws)
#                 if not self.rooms[chat_id]:
#                     self.rooms.pop(chat_id, None)
#
#     async def broadcast(self, chat_id: int, message: dict) -> None:
#         conns = list(self.rooms.get(chat_id, []))
#         text = json.dumps(message, ensure_ascii=False)
#         for ws in conns:
#             try:
#                 await ws.send_text(text)
#             except RuntimeError:
#                 pass


class WSConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.connections.setdefault(user_id, set()).add(ws)

    async def disconnect(self, user_id: int, ws: WebSocket):
        async with self.lock:
            if user_id in self.connections and ws in self.connections[user_id]:
                self.connections[user_id].remove(ws)
                if not self.connections[user_id]:
                    self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, data: dict):
        async with self.lock:
            conns = self.connections.get(user_id, set()).copy()
        text = json.dumps(data, ensure_ascii=False)
        for ws in conns:
            try:
                await ws.send_text(text)
            except Exception:
                pass

    async def broadcast_to_users(self, user_ids: list[int], data: dict):
        for uid in user_ids:
            await self.send_to_user(uid, data)
