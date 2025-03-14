from __future__ import annotations

from dataclasses import dataclass

from app.services.game_manager.models.enums import GameTile


@dataclass
class GameWinningConditions:
    winning_tile: GameTile | None
    is_discarded: bool
    is_last_tile_in_the_game: bool
    is_last_tile_of_its_kind: bool
    is_replacement_tile: bool
    is_robbing_the_kong: bool

    @staticmethod
    def create_default_conditions() -> GameWinningConditions:
        return GameWinningConditions(
            winning_tile=None,
            is_discarded=False,
            is_last_tile_in_the_game=False,
            is_last_tile_of_its_kind=False,
            is_replacement_tile=False,
            is_robbing_the_kong=False,
        )
