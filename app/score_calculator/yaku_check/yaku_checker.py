from abc import abstractmethod
from typing import ClassVar

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Yaku
from app.score_calculator.utility.utility import YAKU_POINT


class YakuChecker:
    def __init__(self, yaku: Yaku):
        self.yaku = yaku

    SINGLE: ClassVar[int] = 1
    DOUBLE: ClassVar[int] = 2
    TRIPLE: ClassVar[int] = 3
    FOUR: ClassVar[int] = 4
    SEVEN: ClassVar[int] = 7
    NUMBER_SIZE: ClassVar[int] = 9
    WIND_SIZE: ClassVar[int] = 4
    DRAGON_SIZE: ClassVar[int] = 3
    NUMBER_TYPE_COUNT: ClassVar[int] = 3
    ALL_TYPE_COUNT: ClassVar[int] = 5
    HAND_SIZE: ClassVar[int] = 14
    MAX_SEQUENCE_START_POINT: ClassVar[int] = 7
    MIN_NUM: ClassVar[int] = 1
    MAX_NUM: ClassVar[int] = 9
    TERMINAL_GAP: ClassVar[int] = 6
    STRAIGHT_GAP: ClassVar[int] = 3

    @abstractmethod
    def validate_basic_conditions(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def check_yaku(self) -> bool:
        raise NotImplementedError

    def get_point(self) -> int:
        return YAKU_POINT[self.yaku] if self.check_yaku() else 0


class BlockYakuChecker(YakuChecker):
    def __init__(self, yaku: Yaku, blocks: list[Block]):
        super().__init__(yaku)
        self.blocks = blocks

    def count_type(self) -> int:
        return len({block.tile.get_type() for block in self.blocks})

    def is_closed(self) -> bool:
        return all(not block.is_opened for block in self.blocks)

    def is_all_sequence(self) -> bool:
        return all(block.type == BlockType.SEQUENCE for block in self.blocks)

    def is_all_triplet(self) -> bool:
        return all(
            block.type in {BlockType.TRIPLET, BlockType.QUAD} for block in self.blocks
        )

    def is_all_quad(self) -> bool:
        return all(block.type == BlockType.QUAD for block in self.blocks)
