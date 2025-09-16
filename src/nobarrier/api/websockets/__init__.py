from fastapi import APIRouter

from nobarrier.api.websockets.chats import router as ws_chats_router


routers = APIRouter()

routers.include_router(ws_chats_router)
