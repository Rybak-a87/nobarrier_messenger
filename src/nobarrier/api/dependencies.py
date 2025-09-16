from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from nobarrier.core.security import SecurityService, TokenExtractor
from nobarrier.database.session import get_session
from nobarrier.schemas.accounts import UserCheck
from nobarrier.services.auth import AuthService
from nobarrier.services.accounts import UserService
from nobarrier.services.chats import ChatService
from nobarrier.services.websockets import WebSocketService


token_extractor = TokenExtractor()


def get_current_user(token: str = Depends(token_extractor)) -> UserCheck:
    return SecurityService().get_current_user(token)


def get_current_admin(token: str = Depends(token_extractor)) -> UserCheck:
    return SecurityService().get_current_admin(token)


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def get_chat_service(session: AsyncSession = Depends(get_session)) -> ChatService:
    return ChatService(session)


def get_websocket_service(session: AsyncSession = Depends(get_session)) -> WebSocketService:
    return WebSocketService(session)
