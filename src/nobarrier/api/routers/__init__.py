from fastapi import APIRouter
from nobarrier.api.routers.accounts import router as accounts_router
from nobarrier.api.routers.auth import router as auth_router
from nobarrier.api.routers.chats import router as chats_router


routers = APIRouter()

routers.include_router(auth_router)
routers.include_router(accounts_router)
routers.include_router(chats_router)
