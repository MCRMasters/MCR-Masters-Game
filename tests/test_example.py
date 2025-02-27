from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.score_calculator.hand.hand import Hand
from app.score_calculator.yaku_check.blocks_yaku_checker import BlocksYakuChecker
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
Z555: Final[Block] = Block(BlockType.TRIPLET, Tile.Z5)
Z7777: Final[Block] = Block(BlockType.QUAD, Tile.Z7)
S1111: Final[Block] = Block(BlockType.QUAD, Tile.S1)
M111: Final[Block] = Block(BlockType.TRIPLET, Tile.M1)


def test_block_yaku_checker():
    assert Yaku.MixedDoubleChow == BlocksYakuChecker([M123, S123]).yaku
    assert Yaku.PureDoubleChow == BlocksYakuChecker([M123, M123]).yaku
    assert Yaku.ShortStraight == BlocksYakuChecker([M123, M456]).yaku
    assert Yaku.TwoTerminalChows == BlocksYakuChecker([M123, M789]).yaku
    assert Yaku.TwoDragonsPungs == BlocksYakuChecker([Z555, Z7777]).yaku
    assert Yaku.DoublePung == BlocksYakuChecker([S1111, M111]).yaku
    hand = raw_string_to_hand_class("445566m556677p55s")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert Yaku.AllFives == BlocksYakuChecker(blocks).yaku
    hand = raw_string_to_hand_class("123m789s111p11z[7777z]")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert Yaku.OutsideHand == BlocksYakuChecker(blocks).yaku
