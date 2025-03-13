from dataclasses import dataclass

from app.services.game_manager.models.enums import GameTile


@dataclass
class GameWinningConditions:
    winning_tile: GameTile
    is_discarded: bool
    is_last_tile_in_the_game: bool
    is_last_tile_of_its_kind: bool
    is_replacement_tile: bool
    is_robbing_the_kong: bool
