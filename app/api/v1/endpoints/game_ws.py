# app/api/v1/endpoints/game_ws_router.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from fastapi.responses import JSONResponse
from app.core.room_manager import RoomManager
from app.dependencies.room_manager import get_room_manager
import urllib.parse

router = APIRouter()

@router.post("/games/start")
async def start_game(
    room_manager: RoomManager = Depends(get_room_manager),
) -> JSONResponse:
    """
    게임을 시작하고, WebSocket URL(쿼리 포함)을 반환합니다.
    """
    try:
        game_id: int = await room_manager.generate_game_id()
        # 인증 정보(예: JWT 토큰)도 room_manager 에서 꺼낼 수 있도록
        token = room_manager._auth_token  # 혹은 PlayerDataManager 에서
        uid   = room_manager._user_id     # 필요에 따라 가져오세요
        nick  = room_manager._nickname

        base = f"wss://mcrs.duckdns.org/game/api/v1/games/{game_id}"
        qs = urllib.parse.urlencode({
            "user_id":      uid,
            "nickname":     nick,
            "authorization": token,
        })
        websocket_url = f"{base}?{qs}"

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
    """
    쿼리스트링에서 인증 정보를 꺼내서 연결을 승인합니다.
    """
    # 이 시점에 아직 accept 전이므로 query_params 에 접근 가능합니다.
    params     = websocket.query_params
    user_id    = params.get("user_id")
    nickname   = params.get("nickname")
    token      = params.get("authorization")

    if not user_id or not nickname or not token:
        # 필수 정보가 없으면 바로 닫음
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="missing user_id, nickname, or authorization in query string",
        )
        return

    # token 을 내부로 전파하기 위해, room_manager.connect 시 인자로 넘기거나
    # websocket.state 에 속성으로 붙여 놓으세요.
    # 예: websocket._token = token

    # 이제 연결 수락
    await websocket.accept()

    handler = GameWebSocketHandler(
        websocket=websocket,
        game_id=game_id,
        room_manager=room_manager,
        user_id=user_id,
        user_nickname=nickname,
        token=token,               # 새로 추가된 인자
    )
    await handler.handle_connection()

