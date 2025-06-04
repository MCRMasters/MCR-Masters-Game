# app/core/room_manager.py

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket, status
from starlette.websockets import WebSocketState

from app.dependencies.game_manager import get_game_manager
from app.services.game_manager.models.player import PlayerData

if TYPE_CHECKING:
    from app.services.game_manager.manager import GameManager

logger = logging.getLogger(__name__)


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
            gid = self.next_game_id
            self.next_game_id += 1
            return gid

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
        need_reload: bool = False
        need_start: bool = False
        game_mgr: GameManager | None = None

        async with self.lock:
            if game_id not in self.active_connections:
                self.active_connections[game_id] = {}

            if self.is_connected(game_id, user_id):
                old = self.active_connections[game_id][user_id]
                try:
                    if old.application_state == WebSocketState.CONNECTED:
                        logger.debug(
                            "Game %d: closing old socket for user %s (reconnect)",
                            game_id,
                            user_id,
                        )
                        await old.close(
                            code=status.WS_1011_INTERNAL_ERROR,
                            reason="Reconnecting",
                        )
                except RuntimeError as e:
                    logger.debug(
                        "Game %d: ignore close-error for user %s: %s",
                        game_id,
                        user_id,
                        e,
                    )

            self.active_connections[game_id][user_id] = websocket
            self.id_to_player_data[user_id] = PlayerData(
                uid=user_id,
                nickname=user_nickname,
            )

            if game_id in self.game_managers:
                game_mgr = self.game_managers[game_id]
                need_reload = True
            else:
                from app.services.game_manager.manager import GameManager

                if len(self.active_connections[game_id]) == GameManager.MAX_PLAYERS:
                    gm = get_game_manager(game_id=game_id)
                    players_data = [
                        self.id_to_player_data[uid]
                        for uid in self.active_connections[game_id]
                    ]
                    gm.init_game(players_data=players_data)
                    self.game_managers[game_id] = gm
                    game_mgr = gm
                    need_start = True

        if need_reload and game_mgr:
            try:
                logger.debug(
                    "Game %d: attempting send_reload_data to user %s",
                    game_id,
                    user_id,
                )
                await game_mgr.send_init_game_data(user_id)
                await game_mgr.round_manager.send_reload_data(user_id)
                logger.info(
                    "Game %d: send_reload_data succeeded for user %s",
                    game_id,
                    user_id,
                )
            except Exception:
                logger.exception(
                    "Game %d: send_reload_data failed for user %s",
                    game_id,
                    user_id,
                )

        if need_start and game_mgr:
            task = asyncio.create_task(game_mgr.start_game())
            task.add_done_callback(
                lambda t: logger.error(
                    "Game %d crashed: %s",
                    game_id,
                    t.exception(),
                )
                if t.exception()
                else None,
            )
            self.game_tasks[game_id] = task
            logger.info(
                "Game %d: all players connected, game task started",
                game_id,
            )

    async def disconnect(self, game_id: int, user_id: str) -> None:
        async with self.lock:
            if game_id in self.active_connections:
                self.active_connections[game_id].pop(user_id, None)
                self.id_to_player_data.pop(user_id, None)
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]
                logger.info("Game %d: user %s disconnected", game_id, user_id)
            await self._check_only_bots_left_and_end(game_id)

    async def disconnect_all(self, game_id: int) -> None:
        async with self.lock:
            if game_id in self.active_connections:
                for user_id in self.active_connections[game_id]:
                    user_ws: WebSocket = self.active_connections[game_id][user_id]
                    user_ws.close()
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
            logger.info("Game %d: disconnected all", game_id)
            await self._check_only_bots_left_and_end(game_id)

    async def _check_only_bots_left_and_end(self, game_id: int) -> None:
        async with self.lock:
            if (
                game_id not in self.active_connections
                or not self.active_connections[game_id]
            ):
                return

            all_uids = list(self.active_connections[game_id].keys())
            remaining_nicknames = [
                self.id_to_player_data[uid].nickname
                for uid in all_uids
                if uid in self.id_to_player_data
            ]

        for nick in remaining_nicknames:
            if not nick.startswith("Bot"):
                return

        logger.info("Game %d: only bots remain, end-game", game_id)

        game_mgr = self.game_managers.get(game_id)
        if game_mgr:
            try:
                await game_mgr.submit_game_result()
                logger.info("Game %d: submit_game_result() complete", game_id)
            except Exception:
                logger.exception("Game %d: error on submit_game_result()", game_id)

        await self.disconnect_all(game_id)

    async def broadcast(
        self,
        message: Any,
        game_id: int,
        exclude_user_id: str | None = None,
    ) -> None:
        async with self.lock:
            if game_id not in self.active_connections:
                return
            to_remove: list[str] = []
            for uid, ws in self.active_connections[game_id].items():
                if uid == exclude_user_id:
                    continue
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(
                        "Game %d: send to %s failed, removing: %s",
                        game_id,
                        uid,
                        e,
                    )
                    to_remove.append(uid)
            for uid in to_remove:
                self.active_connections[game_id].pop(uid, None)
                self.id_to_player_data.pop(uid, None)
                logger.info("Game %d: connection for %s cleaned up", game_id, uid)

    async def send_personal_message(
        self,
        message: Any,
        game_id: int,
        user_id: str,
    ) -> None:
        async with self.lock:
            if (
                game_id not in self.active_connections
                or user_id not in self.active_connections[game_id]
            ):
                return
            ws = self.active_connections[game_id][user_id]
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(
                    "Game %d: personal send to %s failed, removing: %s",
                    game_id,
                    user_id,
                    e,
                )
                self.active_connections[game_id].pop(user_id, None)
                self.id_to_player_data.pop(user_id, None)
                logger.info(
                    "Game %d: cleaned up broken personal connection for %s",
                    game_id,
                    user_id,
                )


room_manager = RoomManager()
