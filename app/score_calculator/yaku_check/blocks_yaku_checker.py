from collections.abc import Callable
from functools import cached_property
from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.score_calculator.yaku_check.yaku_checker import YakuChecker


# yaku checker for combination of blocks
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
            3: self.three_blocks_checker,
            2: self.two_blocks_checker,
            1: None,  # Not implemented for single blocks
        }
        block_len = len(self.blocks)
        if block_len not in checkers:
            raise IndexError("Invalid blocks size.")
        if (checker := checkers[block_len]) is None:
            raise NotImplementedError(
                f"Checker for blocks size {block_len} is not implemented",
            )
        self._yaku = checker()

    # one checker per block size
    def five_blocks_checker(self) -> Yaku:
        conditions = [
            (self.is_all_fives, Yaku.AllFives),
            (self.is_outside_hand, Yaku.OutsideHand),
        ]
        return next((yaku for checker, yaku in conditions if checker), Yaku.ERROR)

    def four_blocks_checker(self) -> Yaku:
        conditions = [
            (self.is_big_four_winds, Yaku.BigFourWinds),
            (self.is_little_four_winds, Yaku.LittleFourWinds),
            (self.is_quadruple_chow, Yaku.QuadrupleChow),
            (self.is_four_pure_shifted_chows, Yaku.FourPureShiftedChows),
            (self.is_four_pure_shifted_pungs, Yaku.FourPureShiftedPungs),
        ]
        return next((yaku for checker, yaku in conditions if checker), Yaku.ERROR)

    def three_blocks_checker(self) -> Yaku:
        conditions = [
            (self.is_big_three_dragons, Yaku.BigThreeDragons),
            (self.is_little_three_dragons, Yaku.LittleThreeDragons),
            (self.is_pure_triple_chow, Yaku.PureTripleChow),
            (self.is_pure_shifted_pungs, Yaku.PureShiftedPungs),
            (self.is_pure_shifted_chows, Yaku.PureShiftedChows),
            (self.is_pure_straight, Yaku.PureStraight),
            (self.is_triple_pung, Yaku.TriplePung),
            (self.is_big_three_winds, Yaku.BigThreeWinds),
            (self.is_knitted_straight, Yaku.KnittedStraight),
            (self.is_mixed_triple_chow, Yaku.MixedTripleChow),
            (self.is_mixed_straight, Yaku.MixedStraight),
            (self.is_mixed_shifted_pungs, Yaku.MixedShiftedPungs),
            (self.is_mixed_shifted_chows, Yaku.MixedShiftedChows),
        ]
        return next((yaku for checker, yaku in conditions if checker), Yaku.ERROR)

    def two_blocks_checker(self) -> Yaku:
        conditions = [
            (self.is_two_dragons_pungs, Yaku.TwoDragonsPungs),
            (self.is_double_pung, Yaku.DoublePung),
            (self.is_pure_double_chow, Yaku.PureDoubleChow),
            (self.is_mixed_double_chow, Yaku.MixedDoubleChow),
            (self.is_short_straight, Yaku.ShortStraight),
            (self.is_two_terminal_chows, Yaku.TwoTerminalChows),
        ]
        return next((yaku for checker, yaku in conditions if checker), Yaku.ERROR)

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

    def count_blocks_if(self, condition: Callable[[Block], bool]) -> int:
        return sum(1 for block in self.blocks if condition(block))

    # general yaku checker
    @property
    def is_mixed_same_num_general(self) -> bool:
        return self.tile_type_count == len(self.blocks) and all(
            self.blocks[0].tile.number == block.tile.number for block in self.blocks
        )

    @property
    def is_pure_chow_general(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.tile_type_count == self.SINGLE
            and all(self.blocks[0].tile == block.tile for block in self.blocks)
        )

    @property
    def is_pure_shifted_pungs_general(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_pung)
            and self.tile_type_count == 1
            and self.has_constant_gap(self.SINGLE)
        )

    @property
    def is_pure_shifted_chows_general(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.tile_type_count == 1
            and (
                self.has_constant_gap(self.SINGLE) or self.has_constant_gap(self.DOUBLE)
            )
        )

    @property
    def is_big_winds_general(self) -> bool:
        return self.validate_all_properties(lambda x: x.is_wind, lambda x: x.is_pung)

    @property
    def is_big_dragons_general(self) -> bool:
        return self.validate_all_properties(lambda x: x.is_dragon, lambda x: x.is_pung)

    # three blocks checker
    @property
    def is_big_three_dragons(self) -> bool:
        return self.is_big_dragons_general

    @property
    def is_little_three_dragons(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_dragon)
            and self.count_blocks_if(lambda x: x.is_pair) == 1
            and self.count_blocks_if(lambda x: x.is_pung) == self.DOUBLE
        )

    @property
    def is_pure_triple_chow(self) -> bool:
        return self.is_pure_chow_general

    @property
    def is_pure_shifted_pungs(self) -> bool:
        return self.is_pure_shifted_pungs_general

    @property
    def is_pure_shifted_chows(self) -> bool:
        return self.is_pure_shifted_chows_general

    @property
    def is_pure_straight(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.tile_type_count == 1
            and self.has_constant_gap(self.STRAIGHT_GAP)
        )

    @property
    def is_triple_pung(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_pung)
            and self.tile_type_count == self.TRIPLE
            and self.count_blocks_if(
                lambda x: x.tile.number == self.blocks[0].tile.number,
            )
            == self.TRIPLE
        )

    @property
    def is_big_three_winds(self) -> bool:
        return self.is_big_winds_general

    @property
    def is_knitted_straight(self) -> bool:
        return (
            self.validate_all_properties(
                lambda x: x.is_number,
                lambda x: x.type == BlockType.KNITTED,
            )
            and self.tile_type_count == self.TRIPLE
            and self.has_constant_gap(1)
        )

    @property
    def is_mixed_triple_chow(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.is_mixed_same_num_general
        )

    @property
    def is_mixed_straight(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.tile_type_count == self.TRIPLE
            and self.has_constant_gap(self.STRAIGHT_GAP)
        )

    @property
    def is_mixed_shifted_pungs(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_pung)
            and self.tile_type_count == self.TRIPLE
            and self.has_constant_gap(self.SINGLE)
        )

    @property
    def is_mixed_shifted_chows(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.tile_type_count == self.TRIPLE
            and (
                self.has_constant_gap(self.SINGLE) or self.has_constant_gap(self.DOUBLE)
            )
        )

    # two blocks checker
    @property
    def is_two_dragons_pungs(self) -> bool:
        return self.validate_all_properties(lambda x: x.is_dragon, lambda x: x.is_pung)

    @property
    def is_double_pung(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_pung)
            and self.is_mixed_same_num_general
        )

    @property
    def is_pure_double_chow(self) -> bool:
        return self.is_pure_chow_general

    @property
    def is_mixed_double_chow(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and self.is_mixed_same_num_general
        )

    @property
    def is_short_straight(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and len(self.blocks) == self.DOUBLE
            and self.has_constant_gap(self.STRAIGHT_GAP)
        )

    @property
    def is_two_terminal_chows(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_number, lambda x: x.is_sequence)
            and len(self.blocks) == self.DOUBLE
            and self.has_constant_gap(self.TERMINAL_GAP)
        )

    # four blocks checker
    @property
    def is_big_four_winds(self) -> bool:
        return self.is_big_winds_general

    @property
    def is_little_four_winds(self) -> bool:
        return (
            self.validate_all_properties(lambda x: x.is_wind)
            and self.count_blocks_if(lambda x: x.is_pair) == 1
            and self.count_blocks_if(lambda x: x.is_pung) == self.TRIPLE
        )

    @property
    def is_quadruple_chow(self) -> bool:
        return self.is_pure_chow_general

    @property
    def is_four_pure_shifted_pungs(self) -> bool:
        return self.is_pure_shifted_pungs_general

    @property
    def is_four_pure_shifted_chows(self) -> bool:
        return self.is_pure_shifted_chows_general

    # five blocks checker
    @property
    def is_outside_hand(self) -> bool:
        return self.validate_all_properties(lambda x: x.has_outside)

    @property
    def is_all_fives(self) -> bool:
        return self.validate_all_properties(lambda x: x.has_five)
