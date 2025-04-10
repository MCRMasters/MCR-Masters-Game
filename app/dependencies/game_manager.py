from typing import TYPE_CHECKING

from app.core.network_service import NetworkService
from app.dependencies.network_service import get_network_service

if TYPE_CHECKING:
    from app.services.game_manager.models.manager import GameManager


def get_game_manager(game_id: int) -> "GameManager":
    from app.services.game_manager.models.manager import GameManager

    network_service: NetworkService = get_network_service()
    return GameManager(game_id=game_id, network_service=network_service)
