from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from fastapi.encoders import jsonable_encoder

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
        message_with_ts = {
            **message,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        json_message = jsonable_encoder(message_with_ts)
        await self.room_manager.send_personal_message(
            message=json_message,
            game_id=game_id,
            user_id=user_id,
        )
        await self.room_manager.record_personal_message(game_id, json_message)

    async def broadcast(
        self,
        message: dict[str, Any],
        game_id: int,
        exclude_user_id: str | None = None,
    ) -> None:
        message_with_ts = {
            **message,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        json_message = jsonable_encoder(message_with_ts)
        await self.room_manager.broadcast(
            message=json_message,
            game_id=game_id,
            exclude_user_id=exclude_user_id,
        )
        await self.room_manager.record_broadcast(game_id, json_message)
