from collections import deque
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, WebSocket, status
from starlette.websockets import WebSocketDisconnect

from app.core.room_manager import RoomManager
from app.dependencies.room_manager import get_room_manager
from app.schemas.watch import WatchGame, WatchGameUser
from app.schemas.ws import MessageEventType

router = APIRouter()


@router.get(
    "/games/watch",
    response_model=list[WatchGame],
    status_code=status.HTTP_200_OK,
)
async def list_watchable_games(
    room_manager: RoomManager = Depends(get_room_manager),
) -> list[WatchGame]:
    result: list[WatchGame] = []
    for gid, conns in room_manager.active_connections.items():
        users = [
            WatchGameUser(
                uid=uid,
                nickname=room_manager.id_to_player_data[uid].nickname,
            )
            for uid in conns
        ]
        result.append(
            WatchGame(
                game_id=gid,
                start_time=room_manager.game_start_times.get(
                    gid,
                    datetime.now(UTC),
                ).isoformat(),
                users=users,
            ),
        )
    return result


@router.websocket("/games/{game_id}/watch")
async def watch_game_ws(
    websocket: WebSocket,
    game_id: int,
    room_manager: RoomManager = Depends(get_room_manager),
) -> None:
    await websocket.accept()
    room_manager.watchers.setdefault(game_id, []).append(websocket)

    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=5)
    history = room_manager.watch_history.get(game_id, deque())
    snaps = [
        (ts, msg)
        for ts, msg in history
        if ts <= cutoff and msg.get("event") == MessageEventType.WATCH_RELOAD_DATA
    ]
    if snaps:
        _, snapshot = max(snaps, key=lambda x: x[0])
        await websocket.send_json(snapshot)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_manager.watchers[game_id].remove(websocket)
