from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand
from app.score_calculator.yaku_check.block_yaku.mixed_double_chow import (
    MixedDoubleChowChecker,
)
from app.score_calculator.yaku_check.block_yaku.pure_double_chow import (
    PureDoubleChowChecker,
)
from app.score_calculator.yaku_check.block_yaku.short_straight import (
    ShortStraightChecker,
)
from app.score_calculator.yaku_check.block_yaku.two_terminal_chows import (
    TwoTerminalChowsChecker,
)
from tests.test_utils import print_blocks, raw_string_to_hand_class


def test_sample():
    assert True


def print_hand(hand1: Hand):
    print(hand1)


def test_print_output():
    print_hand(Hand([0] * 34, []))
    print_hand(Hand.create_from_tiles([0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8], []))
    assert True


def test_print_string_to_hand_1():
    print_hand(raw_string_to_hand_class("1112345678999m9m"))
    print_hand(raw_string_to_hand_class("123m123p123s777z11z"))
    print_hand(raw_string_to_hand_class("123m123p123s11z[888p]"))
    print_hand(raw_string_to_hand_class("123m[888p]123p123s11z"))
    assert True


def test_general_hand_parse():
    hand = raw_string_to_hand_class("1112345678999m9m")
    print(hand)
    for blocks in divide_general_shape(hand):
        print_blocks(blocks)
    hand = raw_string_to_hand_class("147m258s369p111m11z")
    print(hand)
    for blocks in divide_general_shape_knitted_sub(hand):
        print_blocks(blocks)
    assert True


M123: Final[Block] = Block(BlockType.SEQUENCE, Tile.M1)
M456: Final[Block] = Block(BlockType.SEQUENCE, Tile.M4)
M789: Final[Block] = Block(BlockType.SEQUENCE, Tile.M7)
P123: Final[Block] = Block(BlockType.SEQUENCE, Tile.P1)
S123: Final[Block] = Block(BlockType.SEQUENCE, Tile.S1)


def test_check_block_yakus():
    assert MixedDoubleChowChecker([M123, S123]).check_yaku()
    assert not MixedDoubleChowChecker([M123, M789]).check_yaku()

    assert PureDoubleChowChecker([M123, M123]).check_yaku()
    assert not PureDoubleChowChecker([M123, M456]).check_yaku()

    assert ShortStraightChecker([M123, M456]).check_yaku()
    assert not ShortStraightChecker([M789, P123]).check_yaku()

    assert TwoTerminalChowsChecker([M123, M789]).check_yaku()
    assert not TwoTerminalChowsChecker([M123, M456]).check_yaku()
