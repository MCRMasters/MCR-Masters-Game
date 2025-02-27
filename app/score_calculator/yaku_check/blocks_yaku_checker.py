from collections.abc import Callable
from functools import cached_property
from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile, Yaku
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
        checkers = {
            5: self.five_blocks_checker,
            4: self.four_blocks_checker,
            3: None,  # Not implemented for triple blocks
            2: self.two_blocks_checker,
            1: None,  # Not implemented for single blocks
        }
        block_len = len(self.blocks)
        if block_len in checkers:
            checker = checkers[block_len]
            if checker is not None:
                self._yaku = checker()
            else:
                raise NotImplementedError(
                    f"Checker for block length {block_len} is not implemented",
                )
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
        conditions = [
            (self.is_two_dragons_pungs, Yaku.TwoDragonsPungs),
            (self.is_double_pung, Yaku.DoublePung),
            (self.is_pure_double_chow, Yaku.PureDoubleChow),
            (self.is_mixed_double_chow, Yaku.MixedDoubleChow),
            (self.is_short_straight, Yaku.ShortStraight),
            (self.is_two_terminal_chows, Yaku.TwoTerminalChows),
        ]
        return next((value for checker, value in conditions if checker), Yaku.ERROR)

    def four_blocks_checker(self) -> Yaku:
        conditions = [
            (self.is_big_four_winds, Yaku.BigFourWinds),
            (self.is_little_four_winds, Yaku.LittleFourWinds),
            (self.is_quadruple_chow, Yaku.QuadrupleChow),
            (self.is_four_pure_shifted_chows, Yaku.FourPureShiftedChows),
            (self.is_four_pure_shifted_pungs, Yaku.FourPureShiftedPungs),
        ]
        return next((value for checker, value in conditions if checker), Yaku.ERROR)

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

    @cached_property
    def tile_numbers(self) -> list[int]:
        return sorted(block.tile.number for block in self.blocks)

    def has_constant_gap(self, gap: int) -> bool:
        return all(
            gap == abs(pair[0] - pair[1])
            for pair in zip(self.tile_numbers, self.tile_numbers[1:])
        )

    def validate_all_condition(self, condition: Callable[[Block], bool]) -> bool:
        return all(condition(block) for block in self.blocks)

    def validate_all_properties(self, *conditions: Callable[[Block], bool]) -> bool:
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
            self.validate_all_properties(lambda x: x.is_sequence)
            and self.tile_type_count == self.SINGLE
            and all(self.blocks[0].tile == block.tile for block in self.blocks)
        )

    # two blocks checker
    @property
    def is_two_dragons_pungs(self) -> bool:
        return self.validate_all_properties(lambda x: x.is_dragon, lambda x: x.is_pung)

    @property
    def is_double_pung(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_pung)
            and self.is_mixed_same_num
        )

    @property
    def is_pure_double_chow(self) -> bool:
        return self.is_pure_chow

    @property
    def is_mixed_double_chow(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_sequence)
            and self.is_mixed_same_num
        )

    @property
    def is_short_straight(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_sequence)
            and len(self.blocks) == self.DOUBLE
            and abs(self.blocks[0].tile - self.blocks[1].tile) == self.STRAIGHT_GAP
        )

    @property
    def is_two_terminal_chows(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_sequence)
            and len(self.blocks) == self.DOUBLE
            and abs(self.blocks[0].tile - self.blocks[1].tile) == self.TERMINAL_GAP
        )

    # four blocks checker
    @property
    def is_big_four_winds(self) -> bool:
        return self.validate_all_properties(lambda x: x.is_wind, lambda x: x.is_pung)

    @property
    def is_little_four_winds(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_wind)
            and sum(1 for block in self.blocks if block.type == BlockType.PAIR) == 1
        )

    @property
    def is_quadruple_chow(self) -> bool:
        return self.is_pure_chow

    @property
    def is_four_pure_shifted_pungs(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_pung)
            and self.tile_type_count == 1
            and self.has_constant_gap(self.SINGLE)
        )

    @property
    def is_four_pure_shifted_chows(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.tile_type_count == 1
            and (
                self.has_constant_gap(self.SINGLE) or self.has_constant_gap(self.DOUBLE)
            )
        )

    # five blocks checker
    @property
    def is_outside_hand(self) -> bool:
        return self.validate_all_properties(lambda x: x.has_outside)

    @property
    def is_all_fives(self) -> bool:
        return self.validate_all_properties(lambda x: x.has_five)
