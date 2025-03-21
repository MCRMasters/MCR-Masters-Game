from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.game_manager.models.manager import GameManager


def get_game_manager(game_id: int) -> "GameManager":
    from app.services.game_manager.models.manager import GameManager

    return GameManager(game_id=game_id)
