from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.room_manager import RoomManager


class NetworkService:
    def __init__(self, room_manager: RoomManager) -> None:
        self.room_manager = room_manager

    async def send_personal_message(
        self,
        message: dict[str, Any],
        game_id: int,
        user_id: str,
    ) -> None:
        await self.room_manager.send_personal_message(message, game_id, user_id)

    async def broadcast(
        self,
        message: dict[str, Any],
        game_id: int,
        exclude_user_id: str | None = None,
    ) -> None:
        await self.room_manager.broadcast(message, game_id, exclude_user_id)
