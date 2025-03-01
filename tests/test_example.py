from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.score_calculator.hand.hand import Hand
from app.score_calculator.yaku_check.blocks_yaku_checker import BlocksYakuChecker
from app.score_calculator.yaku_check.hand_yaku_checker import HandYakuChecker
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
M234: Final[Block] = Block(BlockType.SEQUENCE, Tile.M2)
M345: Final[Block] = Block(BlockType.SEQUENCE, Tile.M3)
M456: Final[Block] = Block(BlockType.SEQUENCE, Tile.M4)
M567: Final[Block] = Block(BlockType.SEQUENCE, Tile.M5)
M789: Final[Block] = Block(BlockType.SEQUENCE, Tile.M7)
P123: Final[Block] = Block(BlockType.SEQUENCE, Tile.P1)
S123: Final[Block] = Block(BlockType.SEQUENCE, Tile.S1)
Z111: Final[Block] = Block(BlockType.TRIPLET, Tile.Z1)
Z222: Final[Block] = Block(BlockType.TRIPLET, Tile.Z2)
Z333: Final[Block] = Block(BlockType.TRIPLET, Tile.Z3)
Z4444: Final[Block] = Block(BlockType.QUAD, Tile.Z4)
Z11: Final[Block] = Block(BlockType.PAIR, Tile.Z1)
Z555: Final[Block] = Block(BlockType.TRIPLET, Tile.Z5)
Z7777: Final[Block] = Block(BlockType.QUAD, Tile.Z7)
S1111: Final[Block] = Block(BlockType.QUAD, Tile.S1)
M111: Final[Block] = Block(BlockType.TRIPLET, Tile.M1)
M222: Final[Block] = Block(BlockType.TRIPLET, Tile.M2)
M333: Final[Block] = Block(BlockType.TRIPLET, Tile.M3)
M4444: Final[Block] = Block(BlockType.QUAD, Tile.M4)
P111: Final[Block] = Block(BlockType.TRIPLET, Tile.P1)
P222: Final[Block] = Block(BlockType.TRIPLET, Tile.P2)
S111: Final[Block] = Block(BlockType.TRIPLET, Tile.S1)
S333: Final[Block] = Block(BlockType.TRIPLET, Tile.S3)
Z666: Final[Block] = Block(BlockType.TRIPLET, Tile.Z6)
Z777: Final[Block] = Block(BlockType.TRIPLET, Tile.Z7)
Z77: Final[Block] = Block(BlockType.PAIR, Tile.Z7)
M147: Final[Block] = Block(BlockType.KNITTED, Tile.M1)
P258: Final[Block] = Block(BlockType.KNITTED, Tile.S2)
S369: Final[Block] = Block(BlockType.KNITTED, Tile.P3)
P234: Final[Block] = Block(BlockType.SEQUENCE, Tile.P2)
S345: Final[Block] = Block(BlockType.SEQUENCE, Tile.S3)
P456: Final[Block] = Block(BlockType.SEQUENCE, Tile.P4)
S789: Final[Block] = Block(BlockType.SEQUENCE, Tile.S7)


def test_hand_yaku_checker():
    hand = raw_string_to_hand_class("123m123s111p222p33p")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.LowerTiles] == HandYakuChecker(blocks).yakus
    hand = raw_string_to_hand_class("123m234s111p222p33p")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.LowerFour] == HandYakuChecker(blocks).yakus
    hand = raw_string_to_hand_class("456m456s444p555p66p")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.MiddleTiles] == HandYakuChecker(blocks).yakus
    hand = raw_string_to_hand_class("789m789s77788899p")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.UpperTiles] == HandYakuChecker(blocks).yakus
    hand = raw_string_to_hand_class("678m789s77788899p")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.UpperFour] == HandYakuChecker(blocks).yakus


def test_block_yaku_checker():
    assert [Yaku.MixedDoubleChow] == BlocksYakuChecker([M123, S123]).yakus
    assert [Yaku.PureDoubleChow] == BlocksYakuChecker([M123, M123]).yakus
    assert [Yaku.ShortStraight] == BlocksYakuChecker([M123, M456]).yakus
    assert [Yaku.TwoTerminalChows] == BlocksYakuChecker([M123, M789]).yakus
    assert [Yaku.TwoDragonsPungs] == BlocksYakuChecker([Z555, Z7777]).yakus
    assert [Yaku.DoublePung] == BlocksYakuChecker([S1111, M111]).yakus

    hand = raw_string_to_hand_class("445566m556677p55s")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.AllFives] == BlocksYakuChecker(blocks).yakus

    hand = raw_string_to_hand_class("123m789s111p11z[7777z]")
    print(hand)
    blocks = divide_general_shape(hand)[0]
    print_blocks(blocks=blocks)
    assert [Yaku.OutsideHand] == BlocksYakuChecker(blocks).yakus

    assert [Yaku.BigFourWinds] == BlocksYakuChecker([Z111, Z222, Z333, Z4444]).yakus
    assert [Yaku.LittleFourWinds] == BlocksYakuChecker([Z11, Z222, Z333, Z4444]).yakus
    assert [Yaku.QuadrupleChow] == BlocksYakuChecker([M123, M123, M123, M123]).yakus
    assert [Yaku.FourPureShiftedPungs] == BlocksYakuChecker(
        [M111, M222, M333, M4444],
    ).yakus
    assert [Yaku.FourPureShiftedChows] == BlocksYakuChecker(
        [M123, M234, M345, M456],
    ).yakus
    assert [Yaku.FourPureShiftedChows] == BlocksYakuChecker(
        [M123, M345, M567, M789],
    ).yakus

    assert [Yaku.BigThreeDragons] == BlocksYakuChecker([Z555, Z666, Z777]).yakus
    assert [Yaku.LittleThreeDragons] == BlocksYakuChecker([Z555, Z666, Z77]).yakus
    assert [Yaku.PureTripleChow] == BlocksYakuChecker([M123, M123, M123]).yakus
    assert [Yaku.PureShiftedPungs] == BlocksYakuChecker([M111, M222, M333]).yakus
    assert [Yaku.PureShiftedChows] == BlocksYakuChecker([M123, M234, M345]).yakus
    assert [Yaku.PureStraight] == BlocksYakuChecker([M123, M456, M789]).yakus
    assert [Yaku.TriplePung] == BlocksYakuChecker([M111, S111, P111]).yakus
    assert [Yaku.BigThreeWinds] == BlocksYakuChecker([Z111, Z222, Z333]).yakus
    assert [Yaku.KnittedStraight] == BlocksYakuChecker([M147, P258, S369]).yakus
    assert [Yaku.MixedTripleChow] == BlocksYakuChecker([M123, P123, S123]).yakus
    assert [Yaku.MixedStraight] == BlocksYakuChecker([M123, P456, S789]).yakus
    assert [Yaku.MixedShiftedPungs] == BlocksYakuChecker([M111, P222, S333]).yakus
    assert [Yaku.MixedShiftedChows] == BlocksYakuChecker([M123, P234, S345]).yakus
