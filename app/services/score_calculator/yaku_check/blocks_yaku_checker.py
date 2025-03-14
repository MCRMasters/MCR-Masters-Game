from collections.abc import Callable
from functools import cached_property
from typing import Final

from app.services.score_calculator.block.block import Block
from app.services.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.services.score_calculator.yaku_check.yaku_checker import YakuChecker


# yaku checker for combination of blocks
class BlocksYakuChecker(YakuChecker):
    def __init__(self, blocks: list[Block]):
        super().__init__()
        self.blocks: list[Block] = blocks
        self._yakus: list[Yaku]
        self.conditions: dict[int, list[tuple[bool, Yaku]]] = {
            2: [
                (self.is_two_dragons_pungs, Yaku.TwoDragonsPungs),
                (self.is_double_pung, Yaku.DoublePung),
                (self.is_pure_double_chow, Yaku.PureDoubleChow),
                (self.is_mixed_double_chow, Yaku.MixedDoubleChow),
                (self.is_short_straight, Yaku.ShortStraight),
                (self.is_two_terminal_chows, Yaku.TwoTerminalChows),
            ],
            3: [
                (self.is_big_three_dragons, Yaku.BigThreeDragons),
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
            ],
            4: [
                (self.is_big_four_winds, Yaku.BigFourWinds),
                (self.is_quadruple_chow, Yaku.QuadrupleChow),
                (self.is_four_pure_shifted_chows, Yaku.FourPureShiftedChows),
                (self.is_four_pure_shifted_pungs, Yaku.FourPureShiftedPungs),
            ],
            5: [
                (self.is_all_fives, Yaku.AllFives),
                (self.is_outside_hand, Yaku.OutsideHand),
                (self.is_little_four_winds, Yaku.LittleFourWinds),
                (self.is_little_three_dragons, Yaku.LittleThreeDragons),
                (self.is_all_types, Yaku.AllTypes),
            ],
        }
        self.set_yakus()

    STRAIGHT_GAP: Final[int] = 3
    TERMINAL_GAP: Final[int] = 6

    @property
    def yakus(self) -> list[Yaku]:
        return self._yakus

    def set_yakus(self) -> None:
        if len(self.blocks) == 5:
            self._yakus = [
                yaku for checker, yaku in self.conditions[len(self.blocks)] if checker
            ]
        else:
            self._yakus = (
                [] if (result := self.blocks_checker()) == Yaku.ERROR else [result]
            )

    def blocks_checker(self) -> Yaku:
        if len(self.blocks) not in self.conditions:
            raise IndexError("Invalid blocks size.")
        return next(
            (yaku for checker, yaku in self.conditions[len(self.blocks)] if checker),
            Yaku.ERROR,
        )

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
    def first_tile_numbers(self) -> list[int]:
        return sorted(block.tile.number for block in self.blocks)

    def has_constant_gap(self, gap: int) -> bool:
        return all(
            gap == abs(pair[0] - pair[1])
            for pair in zip(self.first_tile_numbers, self.first_tile_numbers[1:])
        )

    def validate_blocks(self, condition: Callable[[Block], bool]) -> bool:
        return all(condition(block) for block in self.blocks)

    def count_blocks_if(self, condition: Callable[[Block], bool]) -> int:
        return sum(1 for block in self.blocks if condition(block))

    # general yaku checker
    @property
    def _is_mixed_same_num(self) -> bool:
        return self.tile_type_count == len(self.blocks) and all(
            self.blocks[0].tile.number == block.tile.number for block in self.blocks
        )

    @property
    def _is_pure_chow(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self.tile_type_count == 1
            and all(self.blocks[0].tile == block.tile for block in self.blocks)
        )

    @property
    def _is_pure_shifted_pungs(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_pung)
            and self.tile_type_count == 1
            and self.has_constant_gap(1)
        )

    @property
    def _is_pure_shifted_chows(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self.tile_type_count == 1
            and (self.has_constant_gap(1) or self.has_constant_gap(2))
        )

    @property
    def _is_big_winds(self) -> bool:
        return self.validate_blocks(lambda x: x.is_wind and x.is_pung)

    @property
    def _is_big_dragons(self) -> bool:
        return self.validate_blocks(lambda x: x.is_dragon and x.is_pung)

    # three blocks checker
    @property
    def is_big_three_dragons(self) -> bool:
        return self._is_big_dragons

    @property
    def is_little_three_dragons(self) -> bool:
        return (
            self.count_blocks_if(lambda x: x.is_dragon and x.is_pair) == 1
            and self.count_blocks_if(lambda x: x.is_dragon and x.is_pung) == 2
        )

    @property
    def is_pure_triple_chow(self) -> bool:
        return self._is_pure_chow

    @property
    def is_pure_shifted_pungs(self) -> bool:
        return self._is_pure_shifted_pungs

    @property
    def is_pure_shifted_chows(self) -> bool:
        return self._is_pure_shifted_chows

    @property
    def is_pure_straight(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self.tile_type_count == 1
            and self.has_constant_gap(self.STRAIGHT_GAP)
        )

    @property
    def is_triple_pung(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_pung)
            and self.tile_type_count == 3
            and self.count_blocks_if(
                lambda x: x.tile.number == self.blocks[0].tile.number,
            )
            == 3
        )

    @property
    def is_big_three_winds(self) -> bool:
        return self._is_big_winds

    @property
    def is_knitted_straight(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.type == BlockType.KNITTED)
            and self.tile_type_count == 3
            and self.has_constant_gap(1)
        )

    @property
    def is_mixed_triple_chow(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self._is_mixed_same_num
        )

    @property
    def is_mixed_straight(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self.tile_type_count == 3
            and self.has_constant_gap(self.STRAIGHT_GAP)
        )

    @property
    def is_mixed_shifted_pungs(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_pung)
            and self.tile_type_count == 3
            and self.has_constant_gap(1)
        )

    @property
    def is_mixed_shifted_chows(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self.tile_type_count == 3
            and self.has_constant_gap(1)
        )

    # two blocks checker
    @property
    def is_two_dragons_pungs(self) -> bool:
        return self.validate_blocks(lambda x: x.is_dragon and x.is_pung)

    @property
    def is_double_pung(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_pung)
            and self._is_mixed_same_num
        )

    @property
    def is_pure_double_chow(self) -> bool:
        return self._is_pure_chow

    @property
    def is_mixed_double_chow(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number and x.is_sequence)
            and self._is_mixed_same_num
        )

    @property
    def is_short_straight(self) -> bool:
        return (
            self.validate_blocks(
                lambda x: x.is_number and x.is_sequence,
            )
            and self.tile_type_count == 1
            and self.has_constant_gap(self.STRAIGHT_GAP)
        )

    @property
    def is_two_terminal_chows(self) -> bool:
        return (
            self.validate_blocks(
                lambda x: x.is_number and x.is_sequence,
            )
            and self.tile_type_count == 1
            and self.has_constant_gap(self.TERMINAL_GAP)
        )

    # four blocks checker
    @property
    def is_big_four_winds(self) -> bool:
        return self._is_big_winds

    @property
    def is_little_four_winds(self) -> bool:
        return (
            self.count_blocks_if(lambda x: x.is_wind and x.is_pair) == 1
            and self.count_blocks_if(lambda x: x.is_wind and x.is_pung) == 3
        )

    @property
    def is_quadruple_chow(self) -> bool:
        return self._is_pure_chow

    @property
    def is_four_pure_shifted_pungs(self) -> bool:
        return self._is_pure_shifted_pungs

    @property
    def is_four_pure_shifted_chows(self) -> bool:
        return self._is_pure_shifted_chows

    # five blocks checker
    @property
    def is_outside_hand(self) -> bool:
        return self.validate_blocks(lambda x: x.has_outside)

    @property
    def is_all_fives(self) -> bool:
        return self.validate_blocks(lambda x: x.has_five)

    @property
    def is_all_types(self) -> bool:
        return self.tile_type_count == 5
