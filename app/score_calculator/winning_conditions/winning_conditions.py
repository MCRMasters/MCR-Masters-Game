# hand.py
from dataclasses import dataclass

from app.score_calculator.enums.enums import Tile, Wind


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
