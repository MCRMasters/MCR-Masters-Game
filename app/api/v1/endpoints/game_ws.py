from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, status
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.game_websocket_handler import GameWebSocketHandler
from app.core.room_manager import RoomManager
from app.dependencies.room_manager import get_room_manager

router = APIRouter()


@router.post("/games/start")
async def start_game(
    request: Request,
    room_manager: RoomManager = Depends(get_room_manager),
) -> JSONResponse:
    try:
        game_id: int = await room_manager.generate_game_id()
        websocket_url: str = f"ws://{request.url.netloc}/api/v1/games/{game_id}"
        return JSONResponse(content={"websocket_url": websocket_url})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.websocket("/games/{game_id}")
async def game_websocket_endpoint(
    websocket: WebSocket,
    game_id: int,
    room_manager: RoomManager = Depends(get_room_manager),
) -> None:
    user_id = websocket.headers.get("user_id")
    nickname = websocket.headers.get("nickname")

    if not user_id or not nickname:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="user_id or nickname header missing",
        )
        return

    await websocket.accept()

    handler = GameWebSocketHandler(
        websocket=websocket,
        game_id=game_id,
        room_manager=room_manager,
        user_id=user_id,
        user_nickname=nickname,
    )
    await handler.handle_connection()
