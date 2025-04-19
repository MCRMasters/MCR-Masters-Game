# app/api/v1/endpoints/game_ws_router.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from fastapi.responses import JSONResponse
from app.core.room_manager import RoomManager
from app.dependencies.room_manager import get_room_manager
from app.api.v1.endpoints.game_websocket_handler import GameWebSocketHandler
import urllib.parse

router = APIRouter()


@router.post("/games/start")
async def start_game(
    room_manager: RoomManager = Depends(get_room_manager),
) -> JSONResponse:
    """
    게임을 시작하고, WebSocket URL(쿼리 포함)을 반환합니다.
    print() 디버깅 추가
    """
    print("▶ start_game 호출됨")
    try:
        # 1) 게임 ID 생성
        game_id: int = await room_manager.generate_game_id()
        print(f"생성된 game_id: {game_id}")

        base = f"wss://mcrs.duckdns.org/game/api/v1/games/{game_id}"

        websocket_url = f"{base}"
        print(f"최종 websocket_url: {websocket_url}")

        # 4) 응답 반환
        return JSONResponse(content={"websocket_url": websocket_url})
    except Exception as e:
        print("❌ start_game 처리 중 예외 발생:", str(e))
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

    if not user_id or not nickname:
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
    )
    await handler.handle_connection()

