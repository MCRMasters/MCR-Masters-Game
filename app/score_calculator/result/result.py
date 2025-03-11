from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Yaku
from app.score_calculator.utility.utility import YAKU_POINT
from app.score_calculator.yaku_check.blocks_yaku_checker import BlocksYakuChecker


@dataclass(order=True)
class ScoreResult:
    total_score: int = field(default=0, compare=True)
    yaku_score_list: list[tuple[Yaku, int]] = field(default_factory=list, compare=False)

    def add_yaku(self, yaku: Yaku, count: int) -> None:
        score = YAKU_POINT[yaku] * count
        self.yaku_score_list.append((yaku, score))
        self.total_score += score


@dataclass
class ScoringContext:
    blocks: list[Block]
    used_block_flag: list[set[Yaku]]

    def get_yakus(self) -> list[Yaku]:
        result: list[Yaku] = []
        for length in (4, 3, 2):
            stack: list[tuple[int, ...]] = list(combinations(range(4), length))
            while stack:
                combination: tuple[int, ...] = stack.pop()
                if all(self.used_block_flag[i] for i in combination):
                    continue
                if (
                    yakus := BlocksYakuChecker(
                        [self.blocks[i] for i in combination],
                    ).yakus
                ) and not any(yakus[0] in self.used_block_flag[i] for i in combination):
                    result += yakus
                    if length == 2:
                        stack.extend(
                            new_combination
                            for new_combination in list(combinations(range(4), length))
                            if (
                                new_combination != combination
                                and (
                                    combination[0] in set(new_combination)
                                    or combination[1] in set(new_combination)
                                )
                            )
                        )
                    for i in combination:
                        self.used_block_flag[i].add(yakus[0])
                    if length != 2:
                        break
        return result

    @staticmethod
    def create_from_blocks(
        blocks: list[Block],
    ) -> ScoringContext:
        used_block_flag: list[set[Yaku]] = [set() for _ in range(len(blocks))]
        return ScoringContext(
            blocks=blocks,
            used_block_flag=used_block_flag,
        )
