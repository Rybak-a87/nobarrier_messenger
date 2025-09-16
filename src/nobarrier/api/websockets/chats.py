from typing import Annotated

from fastapi import APIRouter, WebSocket, Depends

from nobarrier.api.dependencies import get_websocket_service
from nobarrier.services.websockets import WebSocketService


router = APIRouter(
    prefix="/ws",
    tags=["Web Socket"],
    # dependencies=[Depends(get_current_user)]
)


@router.websocket("/message/{chat_id}")
async def ws_user(websocket: WebSocket, chat_id: int, service: Annotated[WebSocketService, Depends(get_websocket_service)]):
    await service.web_socket_user(web_socket=websocket, chat_id=chat_id)


# @router.websocket("/chats/{chat_id}")
# async def ws_chat(web_socket: WebSocket, chat_id: int, service: Annotated[WebSocketService, Depends(get_websocket_service)]) -> None:
#     return await service.web_socket_chat(web_socket=web_socket, chat_id=chat_id)
