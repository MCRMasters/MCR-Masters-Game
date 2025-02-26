from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand
from app.score_calculator.yaku_check.block_yaku.mixed_double_chow import (
    check_mixed_double_chow,
)
from app.score_calculator.yaku_check.block_yaku.pure_double_chow import (
    check_pure_double_chow,
)
from app.score_calculator.yaku_check.block_yaku.short_straight import (
    check_short_straight,
)
from app.score_calculator.yaku_check.block_yaku.two_terminal_chows import (
    check_two_terminal_chows,
)
from tests.test_utils import raw_string_to_hand_class


def test_sample():
    assert True


def print_hand(hand1: Hand):
    print(hand1)


def test_print_output():
    print_hand(Hand([0] * 34, []))
    print_hand(Hand.create_from_tiles([0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8], []))
    assert True


def test_print_string_to_hand_1():
    print_hand(raw_string_to_hand_class("1112345678999m"))
    print_hand(raw_string_to_hand_class("123m123p123s777z11z"))
    print_hand(raw_string_to_hand_class("123m123p123s11z[888p]"))
    print_hand(raw_string_to_hand_class("123m[888p]123p123s11z"))
    assert True


M123: Final[Block] = Block(BlockType.SEQUENCE, Tile.M1)
M456: Final[Block] = Block(BlockType.SEQUENCE, Tile.M4)
M789: Final[Block] = Block(BlockType.SEQUENCE, Tile.M7)
P123: Final[Block] = Block(BlockType.SEQUENCE, Tile.P1)
S123: Final[Block] = Block(BlockType.SEQUENCE, Tile.S1)


def test_check_block_yakus():
    assert check_mixed_double_chow([M123, S123])
    assert not check_mixed_double_chow([M123, M789])
    assert check_pure_double_chow([M123, M123])
    assert not check_pure_double_chow([M123, M456])
    assert check_short_straight([M123, M456])
    assert not check_short_straight([M789, P123])
    assert check_two_terminal_chows([M123, M789])
    assert not check_two_terminal_chows([M123, M456])
