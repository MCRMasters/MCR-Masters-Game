from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket, status

from app.dependencies.game_manager import get_game_manager
from app.services.game_manager.models.player import PlayerData

if TYPE_CHECKING:
    from app.services.game_manager.models.manager import GameManager


class RoomManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, dict[str, WebSocket]] = {}
        self.game_managers: dict[int, GameManager] = {}
        self.game_tasks: dict[int, asyncio.Task] = {}
        self.id_to_player_data: dict[str, PlayerData] = {}
        self.lock = asyncio.Lock()
        self.next_game_id: int = 1

    async def generate_game_id(self) -> int:
        async with self.lock:
            game_id = self.next_game_id
            self.next_game_id += 1
            return game_id

    def is_connected(self, game_id: int, user_id: str) -> bool:
        return (
            game_id in self.active_connections
            and user_id in self.active_connections[game_id]
        )

    async def connect(
        self,
        websocket: WebSocket,
        game_id: int,
        user_id: str,
        user_nickname: str,
    ) -> None:
        async with self.lock:
            if game_id not in self.active_connections:
                self.active_connections[game_id] = {}
            if self.is_connected(game_id, user_id):
                existing_ws = self.active_connections[game_id][user_id]
                await existing_ws.close(
                    code=status.WS_1011_INTERNAL_ERROR,
                    reason="Reconnecting",
                )
            self.active_connections[game_id][user_id] = websocket
            self.id_to_player_data[user_id] = PlayerData(
                uid=user_id,
                nickname=user_nickname,
            )
            from app.services.game_manager.models.manager import GameManager

            if len(self.active_connections[game_id]) == GameManager.MAX_PLAYERS:
                players_data: list[PlayerData] = [
                    self.id_to_player_data[uid]
                    for uid in self.active_connections[game_id]
                ]
                self.game_managers[game_id] = get_game_manager(game_id=game_id)
                self.game_managers[game_id].init_game(players_data=players_data)

                task = asyncio.create_task(self.game_managers[game_id].start_game())
                task.add_done_callback(
                    lambda t: print(f"Task finished with exception: {t.exception()}")
                    if t.exception()
                    else None,
                )

                self.game_tasks[game_id] = task

    async def disconnect(self, game_id: int, user_id: str) -> None:
        async with self.lock:
            if game_id in self.active_connections:
                self.active_connections[game_id].pop(user_id, None)
                self.id_to_player_data.pop(user_id, None)
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]

    async def broadcast(
        self,
        message: Any,
        game_id: int,
        exclude_user_id: str | None = None,
    ) -> None:
        async with self.lock:
            if game_id in self.active_connections:
                for uid, connection in self.active_connections[game_id].items():
                    if exclude_user_id is None or uid != exclude_user_id:
                        try:
                            await connection.send_json(message)
                        except Exception as e:
                            print(f"Failed to send message to {uid}: {e}")

    async def send_personal_message(
        self,
        message: Any,
        game_id: int,
        user_id: str,
    ) -> None:
        async with self.lock:
            if (
                game_id in self.active_connections
                and user_id in self.active_connections[game_id]
            ):
                try:
                    await self.active_connections[game_id][user_id].send_json(message)
                except Exception as e:
                    print(f"Failed to send personal message to {user_id}: {e}")


room_manager = RoomManager()
