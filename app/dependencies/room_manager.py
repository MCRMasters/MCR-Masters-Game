from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.room_manager import RoomManager


def get_room_manager() -> "RoomManager":
    from app.core.room_manager import room_manager

    return room_manager
