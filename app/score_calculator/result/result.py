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
class BlockRelationScoringContext:
    blocks: list[Block]
    used_block_flag: list[set[Yaku]]

    def get_yakus(self) -> list[Yaku]:
        return (
            self._get_yakus_by_length(4)
            + self._get_yakus_by_length(3)
            + self._get_yakus_of_two_blocks()
        )

    def _get_yakus_by_length(self, length: int) -> list[Yaku]:
        result: list[Yaku] = []
        for combination in combinations(range(4), length):
            if all(self.used_block_flag[i] for i in combination):
                continue
            current_blocks: list[Block] = [self.blocks[i] for i in combination]
            yakus: list[Yaku] = BlocksYakuChecker(current_blocks).yakus
            if yakus and not any(
                yakus[0] in self.used_block_flag[i] for i in combination
            ):
                result.extend(yakus)
                for i in combination:
                    self.used_block_flag[i].add(yakus[0])
                break
        return result

    def _get_yakus_of_two_blocks(self) -> list[Yaku]:
        result: list[Yaku] = []
        stack: list[tuple[int, int]] = list(combinations(range(4), 2))
        while stack:
            combination = stack.pop()
            if all(self.used_block_flag[i] for i in combination):
                continue
            current_blocks = [self.blocks[i] for i in combination]
            yakus = BlocksYakuChecker(current_blocks).yakus
            if yakus and not any(
                yakus[0] in self.used_block_flag[i] for i in combination
            ):
                result.extend(yakus)
                for i in combination:
                    self.used_block_flag[i].add(yakus[0])
                for new_combination in combinations(range(4), 2):
                    if new_combination != combination and (
                        combination[0] in new_combination
                        or combination[1] in new_combination
                    ):
                        stack.append(new_combination)
        return result

    @staticmethod
    def create_from_blocks(
        blocks: list[Block],
    ) -> BlockRelationScoringContext:
        used_block_flag: list[set[Yaku]] = [set() for _ in blocks]
        return BlockRelationScoringContext(
            blocks=blocks,
            used_block_flag=used_block_flag,
        )
