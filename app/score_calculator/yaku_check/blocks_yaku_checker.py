from collections.abc import Callable
from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Tile, Yaku
from app.score_calculator.yaku_check.yaku_checker import YakuChecker


class BlocksYakuChecker(YakuChecker):
    def __init__(self, blocks: list[Block]):
        super().__init__()
        self.blocks: list[Block] = blocks
        self._yaku: Yaku
        self.set_yaku()

    SINGLE: Final[int] = 1
    DOUBLE: Final[int] = 2
    TRIPLE: Final[int] = 3
    FOUR: Final[int] = 4
    FIVE: Final[int] = 5

    STRAIGHT_GAP: Final[int] = 3
    TERMINAL_GAP: Final[int] = 6

    @property
    def yaku(self) -> Yaku:
        return self._yaku

    def set_yaku(self) -> None:
        if len(self.blocks) == self.FIVE:
            self._yaku = self.five_blocks_checker()
        elif len(self.blocks) == self.FOUR or len(self.blocks) == self.TRIPLE:
            raise NotImplementedError
        elif len(self.blocks) == self.DOUBLE:
            self._yaku = self.two_blocks_checker()
        elif len(self.blocks) == self.SINGLE:
            raise NotImplementedError
        else:
            raise IndexError("invalid blocks size")

    # one checker per block size
    def five_blocks_checker(self) -> Yaku:
        result: Yaku = Yaku.ERROR
        if self.is_all_fives:
            result = Yaku.AllFives
        elif self.is_outside_hand:
            result = Yaku.OutsideHand
        return result

    def two_blocks_checker(self) -> Yaku:
        result: Yaku = Yaku.ERROR
        if self.is_two_dragons_pungs:
            result = Yaku.TwoDragonsPungs
        elif self.is_double_pung:
            result = Yaku.DoublePung
        elif self.is_pure_double_chow:
            result = Yaku.PureDoubleChow
        elif self.is_mixed_double_chow:
            result = Yaku.MixedDoubleChow
        elif self.is_short_straight:
            result = Yaku.ShortStraight
        elif self.is_two_terminal_chows:
            result = Yaku.TwoTerminalChows
        return result

    # utils
    @property
    def tile_type_count(self) -> int:
        return len({block.tile.type for block in self.blocks})

    @property
    def block_type_count(self) -> int:
        return len({block.type for block in self.blocks})

    @property
    def start_tiles(self) -> list[Tile]:
        return [block.tile for block in self.blocks]

    def validate_all_condition(self, condition: Callable[[Block], bool]) -> bool:
        return all(condition.__get__(block) for block in self.blocks)

    def validate_all_conditions(self, *conditions: Callable[[Block], bool]) -> bool:
        return all(self.validate_all_condition(condition) for condition in conditions)

    # general yaku checker
    @property
    def is_mixed_same_num(self) -> bool:
        return self.tile_type_count == len(self.blocks) and all(
            self.blocks[0].tile.number == block.tile.number for block in self.blocks
        )

    @property
    def is_pure_chow(self) -> bool:
        return (
            self.validate_all_condition(Block.is_sequence)
            and self.tile_type_count == self.SINGLE
            and all(self.blocks[0].tile == block.tile for block in self.blocks)
        )

    # two blocks checker
    @property
    def is_two_dragons_pungs(self) -> bool:
        return self.validate_all_conditions(Block.is_dragon, Block.is_triplet)

    @property
    def is_double_pung(self) -> bool:
        return (
            self.validate_all_conditions(Block.is_number, Block.is_triplet)
            and self.is_mixed_same_num
        )

    @property
    def is_pure_double_chow(self) -> bool:
        return self.is_pure_chow

    @property
    def is_mixed_double_chow(self) -> bool:
        return self.validate_all_condition(Block.is_sequence) and self.is_mixed_same_num

    @property
    def is_short_straight(self) -> bool:
        return (
            self.validate_all_conditions(Block.is_sequence)
            and len(self.blocks) == self.DOUBLE
            and abs(self.blocks[0].tile - self.blocks[1].tile) == self.STRAIGHT_GAP
        )

    @property
    def is_two_terminal_chows(self) -> bool:
        return (
            self.validate_all_conditions(Block.is_sequence)
            and len(self.blocks) == self.DOUBLE
            and abs(self.blocks[0].tile - self.blocks[1].tile) == self.TERMINAL_GAP
        )

    # five blocks checker
    @property
    def is_outside_hand(self) -> bool:
        return self.validate_all_condition(Block.has_outside)

    @property
    def is_all_fives(self) -> bool:
        return self.validate_all_condition(Block.has_five)
