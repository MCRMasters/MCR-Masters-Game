from __future__ import annotations

from dataclasses import dataclass

from app.services.game_manager.models.enums import AbsoluteSeat
from app.services.game_manager.models.winning_conditions import GameWinningConditions
from app.services.score_calculator.enums.enums import Tile, Wind


@dataclass
class WinningConditions:
    winning_tile: Tile
    is_discarded: bool
    is_last_tile_in_the_game: bool
    is_last_tile_of_its_kind: bool
    is_replacement_tile: bool
    is_robbing_the_kong: bool
    count_tenpai_tiles: int
    seat_wind: Wind
    round_wind: Wind

    @staticmethod
    def create_from_game_winning_conditions(
        game_winning_conditions: GameWinningConditions,
        seat_wind: AbsoluteSeat,
        round_wind: AbsoluteSeat,
    ) -> WinningConditions:
        if game_winning_conditions.winning_tile is None:
            raise ValueError(
                "[WinningConditions.create_from_game_winning_conditions]tile is none",
            )
        return WinningConditions(
            winning_tile=Tile.create_from_game_tile(
                game_winning_conditions.winning_tile,
            ),
            is_discarded=game_winning_conditions.is_discarded,
            is_last_tile_in_the_game=game_winning_conditions.is_last_tile_in_the_game,
            is_last_tile_of_its_kind=game_winning_conditions.is_last_tile_of_its_kind,
            is_replacement_tile=game_winning_conditions.is_replacement_tile,
            is_robbing_the_kong=game_winning_conditions.is_robbing_the_kong,
            count_tenpai_tiles=1,
            seat_wind=Wind.create_from_absolute_seat(seat_wind),
            round_wind=Wind.create_from_absolute_seat(round_wind),
        )
