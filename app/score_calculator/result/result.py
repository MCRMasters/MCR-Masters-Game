# result.py
from dataclasses import dataclass

from app.score_calculator.winning_conditions.winning_conditions import WinningConditions


@dataclass
class Result:
    yaku_score_list: list[tuple[int, int]]
    tenpai_tiles: list[int]
    winning_conditions: WinningConditions
    highest_score: int = 0
    is_blocks_divided: bool = False
