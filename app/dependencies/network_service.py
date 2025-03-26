from typing import TYPE_CHECKING

from fastapi import Depends

from app.core.network_service import NetworkService
from app.dependencies.room_manager import get_room_manager

if TYPE_CHECKING:
    from app.core.room_manager import RoomManager


def get_network_service(
    room_manager: "RoomManager" = Depends(get_room_manager),
) -> NetworkService:
    return NetworkService(room_manager)
