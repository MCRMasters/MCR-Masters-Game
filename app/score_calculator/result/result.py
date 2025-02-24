# result.py
from __future__ import annotations

from dataclasses import dataclass

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Yaku
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions


@dataclass
class ScoreResult:
    yaku_score_list: list[tuple[int, int]]
    tenpai_tiles: list[int]
    highest_score: int = 0
    is_blocks_divided: bool = False


@dataclass
class ScoringContext:
    blocks: list[Block]
    used_block_flag: list[bool]
    checked_yaku: dict[Yaku, bool]
    winning_conditions: WinningConditions

    @staticmethod
    def create_from_blocks_and_winning_conditions(
        blocks: list[Block],
        winning_conditions: WinningConditions,
    ) -> ScoringContext:
        used_block_flag: list[bool] = [False] * len(blocks)
        checked_yaku: dict[Yaku, bool] = {yaku: False for yaku in Yaku}
        return ScoringContext(
            blocks=blocks,
            used_block_flag=used_block_flag,
            checked_yaku=checked_yaku,
            winning_conditions=winning_conditions,
        )
