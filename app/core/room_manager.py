from typing import Any
from uuid import UUID

from fastapi import WebSocket, status

from app.dependencies.game_manager import get_game_manager
from app.services.game_manager.models.manager import GameManager
from app.services.game_manager.models.player import PlayerData


class RoomManager:
    def __init__(self) -> None:
        # game_id를 키로, 각 게임의 연결을 {user_id: WebSocket} 형태로 관리합니다.
        self.active_connections: dict[int, dict[UUID, WebSocket]] = {}
        self.game_managers: dict[int, GameManager] = {}
        self.id_to_player_data: dict[UUID, PlayerData] = {}

    async def connect(
        self,
        websocket: WebSocket,
        game_id: int,
        user_id: UUID,
        user_nickname: str,
    ) -> None:
        """
        WebSocket 연결을 등록합니다.
        """
        # 해당 game_id에 연결 목록이 없으면 생성
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        # 이미 user_id가 연결되어 있다면 기존 연결 닫기
        if user_id in self.active_connections[game_id]:
            existing_ws = self.active_connections[game_id][user_id]
            await existing_ws.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Reconnecting",
            )
        self.active_connections[game_id][user_id] = websocket
        self.id_to_player_data[user_id] = PlayerData(id=user_id, nickname=user_nickname)
        if len(self.active_connections[game_id]) == GameManager.MAX_PLAYERS:
            player_datas: list[PlayerData] = [
                self.id_to_player_data[uid] for uid in self.active_connections[game_id]
            ]
            self.game_managers[game_id] = get_game_manager()
            self.game_managers[game_id].init_game(player_datas=player_datas)
            self.game_managers[game_id].start_game()

    def disconnect(self, game_id: int, user_id: UUID) -> None:
        """
        WebSocket 연결을 해제합니다.
        """
        if game_id in self.active_connections:
            self.active_connections[game_id].pop(user_id, None)
            self.id_to_player_data.pop(user_id, None)
            # 해당 게임에 연결된 클라이언트가 없으면 game_id 제거
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast(
        self,
        message: Any,
        game_id: int,
        exclude_user_id: UUID | None = None,
    ) -> None:
        """
        해당 game_id에 연결된 모든 WebSocket에 메시지를 전송합니다.
        필요하면 exclude_user_id에 해당하는 클라이언트는 제외합니다.
        """
        if game_id in self.active_connections:
            for uid, connection in self.active_connections[game_id].items():
                if exclude_user_id is None or uid != exclude_user_id:
                    await connection.send_json(message)

    async def send_personal_message(
        self,
        message: Any,
        game_id: int,
        user_id: Any,
    ) -> None:
        """
        특정 user_id에게만 메시지를 전송합니다.
        """
        if (
            game_id in self.active_connections
            and user_id in self.active_connections[game_id]
        ):
            await self.active_connections[game_id][user_id].send_json(message)


# 전역 room_manager 인스턴스를 생성해서 의존성 주입을 통해 사용
room_manager = RoomManager()
