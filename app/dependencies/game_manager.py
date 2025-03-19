from app.services.game_manager.models.manager import GameManager


def get_game_manager() -> GameManager:
    return GameManager()
