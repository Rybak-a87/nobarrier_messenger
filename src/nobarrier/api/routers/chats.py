from typing import Annotated

from fastapi import APIRouter, Depends

from nobarrier.api.dependencies import get_current_user, get_chat_service
from nobarrier.database.models import User
from nobarrier.schemas.chats import ChatCreate, MessageCreate
from nobarrier.services.chats import ChatService


router = APIRouter(
    prefix="/chats",
    tags=["Chats"],
    # dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=dict)
async def create_chat(
    payload: ChatCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
    # session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Create new chat
    \f
    """
    return await service.create_chat(user_id=user.id, member_ids=payload.member_ids, is_group=payload.is_group)


@router.get("/", response_model=list[dict])
async def list_chats(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
):
    """
        List all chats
        \f
    """
    return await service.get_chats(user_id=user.id)


@router.get("/{chat_id}/messages", response_model=list[dict])
async def get_messages(
    chat_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
    limit: int = 50,
    offset: int = 0,
):
    """
    List all messages
    \f
    """
    return await service.get_messages(user_id=user.id, chat_id=chat_id, limit=limit, offset=offset)


@router.post("/{chat_id}/messages", response_model=dict)
async def get_messages(
    chat_id: int,
    payload: MessageCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
):
    """
    Create new messages
    \f
    """
    return await service.send_message(user_id=user.id, chat_id=chat_id, content=payload.content)

