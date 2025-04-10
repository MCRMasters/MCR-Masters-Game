from functools import lru_cache

from app.core.network_service import NetworkService


@lru_cache(maxsize=1)
def get_network_service() -> NetworkService:
    from app.core.room_manager import room_manager

    return NetworkService(room_manager)
