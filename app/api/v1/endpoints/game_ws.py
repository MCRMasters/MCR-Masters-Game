from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, status

from app.api.v1.endpoints.game_websocket_handler import GameWebSocketHandler
from app.core.room_manager import RoomManager
from app.dependencies.room_manager import get_room_manager

router = APIRouter()


@router.websocket("/games/{game_id}")
async def game_websocket_endpoint(
    websocket: WebSocket,
    game_id: int,
    room_manager: RoomManager = Depends(get_room_manager),
):
    user_id_str = websocket.headers.get("user_id")
    nickname = websocket.headers.get("nickname")

    if not user_id_str or not nickname:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="user_id or nickname header missing",
        )
        return

    try:
        user_id = UUID(user_id_str)
    except Exception:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid user_id format",
        )
        return
    handler = GameWebSocketHandler(
        websocket=websocket,
        game_id=game_id,
        room_manager=room_manager,
        user_id=user_id,
        user_nickname=nickname,
    )
    await handler.handle_connection()
