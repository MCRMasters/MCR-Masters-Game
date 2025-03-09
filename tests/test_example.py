from typing import Final

import pytest

from app.score_calculator.block.block import Block
from app.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.score_calculator.divide.seven_pairs_shape import divide_seven_pairs_shape
from app.score_calculator.enums.enums import BlockType, Tile, Wind, Yaku
from app.score_calculator.hand.hand import Hand
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions
from app.score_calculator.yaku_check.blocks_yaku_checker import BlocksYakuChecker
from app.score_calculator.yaku_check.hand_yaku_checker import HandYakuChecker
from app.score_calculator.yaku_check.winning_conditions_yaku_checker import (
    WinningConditionsYakuChecker,
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


def create_default_winning_conditions(
    winning_tile: Tile,
    is_discarded: bool = True,
    count_tenpai_tiles: int = 1,
    seat_wind: Wind = Wind.EAST,
    round_wind: Wind = Wind.EAST,
    **extra_conditions,
):
    defaults = {
        "is_last_tile_in_the_game": False,
        "is_last_tile_of_its_kind": False,
        "is_replacement_tile": False,
        "is_robbing_the_kong": False,
    }
    defaults.update(extra_conditions)
    return WinningConditions(
        winning_tile=winning_tile,
        is_discarded=is_discarded,
        count_tenpai_tiles=count_tenpai_tiles,
        seat_wind=seat_wind,
        round_wind=round_wind,
        is_last_tile_in_the_game=defaults["is_last_tile_in_the_game"],
        is_last_tile_of_its_kind=defaults["is_last_tile_of_its_kind"],
        is_replacement_tile=defaults["is_replacement_tile"],
        is_robbing_the_kong=defaults["is_robbing_the_kong"],
    )


@pytest.mark.parametrize(
    "hand_string, expected_yaku, use_seven_pairs",
    [
        ("123m123s111p222p33p", Yaku.LowerTiles, False),
        ("123m234s111p222p33p", Yaku.LowerFour, False),
        ("456m456s444p555p66p", Yaku.MiddleTiles, False),
        ("789m789s77788899p", Yaku.UpperTiles, False),
        ("678m789s77788899p", Yaku.UpperFour, False),
        ("11223344556677z", Yaku.AllHonors, True),
        ("111999m111999s11p", Yaku.AllTerminals, False),
        ("111999m111222z99s", Yaku.AllTerminalsAndHonors, False),
        ("234456m234s67888p", Yaku.AllSimples, False),
        ("111123m678p78999s", Yaku.NoHonorTiles, False),
    ],
)
def test_hand_yaku_checker(hand_string, expected_yaku, use_seven_pairs):
    hand = raw_string_to_hand_class(hand_string)
    blocks = (
        divide_seven_pairs_shape(hand)
        if use_seven_pairs
        else divide_general_shape(hand)[0]
    )
    winning_conditions = create_default_winning_conditions(blocks[0].tile)
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku",
    [
        ("11112367878999s", Yaku.FullFlush),
        ("111222z67878999s", Yaku.HalfFlush),
        ("111222z678p78999s", Yaku.OneVoidedSuit),
    ],
)
def test_hand_yakus_checker_flush(hand_string, expected_yaku):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    winning_conditions = create_default_winning_conditions(blocks[0].tile)
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku",
    [
        ("[1111z]{2222m}[3333s]{5555p}11p", Yaku.FourKongs),
        ("[1111z]{2222m}[3333s]555p11p", Yaku.ThreeKongs),
        ("111z{2222m}{3333s}555p11p", Yaku.TwoConcealedKongs),
        ("111z[2222m][3333s]555p11p", Yaku.TwoMeldedKongs),
        ("111z222m{3333s}555p11p", Yaku.ConcealedKong),
        ("111z222m[3333s]555p11p", Yaku.MeldedKong),
    ],
)
def test_hand_yakus_checker_kong(hand_string, expected_yaku):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    winning_conditions = create_default_winning_conditions(blocks[0].tile)
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku, winning_conditions",
    [
        (
            "222m333p444s555z66p",
            Yaku.FourConcealedPungs,
            create_default_winning_conditions(winning_tile=Tile.P6, is_discarded=True),
        ),
        (
            "222m333p444s555z66p",
            Yaku.ThreeConcealedPungs,
            create_default_winning_conditions(winning_tile=Tile.Z5, is_discarded=True),
        ),
        (
            "222m333p345p456s66p",
            Yaku.TwoConcealedPungs,
            create_default_winning_conditions(winning_tile=Tile.P3, is_discarded=True),
        ),
    ],
)
def test_concealed_pungs(hand_string, expected_yaku, winning_conditions):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku, winning_conditions, use_seven_pairs",
    [
        (
            "11223344556677m",
            Yaku.SevenShiftedPairs,
            create_default_winning_conditions(winning_tile=Tile.M1, is_discarded=True),
            True,
        ),
        (
            "11112345678999m",
            Yaku.NineGates,
            create_default_winning_conditions(
                winning_tile=Tile.M5,
                is_discarded=False,
                count_tenpai_tiles=9,
            ),
            False,
        ),
        (
            "123m789m123m789m55m",
            Yaku.PureTerminalChows,
            create_default_winning_conditions(winning_tile=Tile.M5, is_discarded=True),
            False,
        ),
        (
            "222m444p666s888m66p",
            Yaku.AllEvenPungs,
            create_default_winning_conditions(winning_tile=Tile.P4, is_discarded=True),
            False,
        ),
        (
            "11223344667788m",
            Yaku.SevenPairs,
            create_default_winning_conditions(winning_tile=Tile.M3, is_discarded=True),
            True,
        ),
        (
            "123m789m123p789p55s",
            Yaku.ThreeSuitedTerminalChows,
            create_default_winning_conditions(winning_tile=Tile.S5, is_discarded=True),
            False,
        ),
        (
            "222m333p444s555z66p",
            Yaku.AllPungs,
            create_default_winning_conditions(winning_tile=Tile.P6, is_discarded=True),
            False,
        ),
        (
            "123m234m345m456m66m",
            Yaku.AllChows,
            create_default_winning_conditions(winning_tile=Tile.M2, is_discarded=True),
            False,
        ),
    ],
)
def test_hand_shape_yakus(
    hand_string,
    expected_yaku,
    winning_conditions,
    use_seven_pairs,
):
    hand = raw_string_to_hand_class(hand_string)
    blocks = (
        divide_seven_pairs_shape(hand)
        if use_seven_pairs
        else divide_general_shape(hand)[0]
    )
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku, winning_conditions",
    [
        (
            "222m333p123s555z66p",
            Yaku.EdgeWait,
            create_default_winning_conditions(winning_tile=Tile.S3, is_discarded=True),
        ),
        (
            "222m333p123s555z66p",
            Yaku.ClosedWait,
            create_default_winning_conditions(winning_tile=Tile.S2, is_discarded=True),
        ),
        (
            "222m333p345p456s66p",
            Yaku.SingleWait,
            create_default_winning_conditions(winning_tile=Tile.P6, is_discarded=True),
        ),
    ],
)
def test_wait(hand_string, expected_yaku, winning_conditions):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku",
    [
        ("222s234s666s888s66z", Yaku.AllGreen),
    ],
)
def test_all_green(hand_string, expected_yaku):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    winning_conditions = create_default_winning_conditions(blocks[0].tile)
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku",
    [
        ("888p999p888s555z99s", Yaku.ReversibleTiles),
    ],
)
def test_reversible_tiles(hand_string, expected_yaku):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    winning_conditions = create_default_winning_conditions(blocks[0].tile)
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku, winning_conditions",
    [
        (
            "222m333p444s555z66p",
            Yaku.DragonPung,
            create_default_winning_conditions(winning_tile=Tile.P6, is_discarded=True),
        ),
        (
            "222m333p444s111z66p",
            Yaku.PrevalentWind,
            create_default_winning_conditions(
                winning_tile=Tile.Z5,
                is_discarded=True,
                round_wind=Wind.EAST,
            ),
        ),
        (
            "222m333p345p111z66p",
            Yaku.SeatWind,
            create_default_winning_conditions(
                winning_tile=Tile.P3,
                is_discarded=True,
                seat_wind=Wind.EAST,
            ),
        ),
    ],
)
def test_one_block_yaku(hand_string, expected_yaku, winning_conditions):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    assert expected_yaku in HandYakuChecker(blocks, winning_conditions).yakus


@pytest.mark.parametrize(
    "hand_string, expected_yaku, winning_conditions",
    [
        (
            "222m333p444s555z66p",
            Yaku.LastTileDraw,
            create_default_winning_conditions(
                winning_tile=Tile.P6,
                is_discarded=False,
                is_last_tile_in_the_game=True,
            ),
        ),
        (
            "222m333p444s555z66p",
            Yaku.LastTileClaim,
            create_default_winning_conditions(
                winning_tile=Tile.P6,
                is_discarded=True,
                is_last_tile_in_the_game=True,
            ),
        ),
        (
            "222m333p345p111z66p",
            Yaku.FullyConcealedHand,
            create_default_winning_conditions(
                winning_tile=Tile.P3,
                is_discarded=False,
                seat_wind=Wind.EAST,
            ),
        ),
        (
            "222m333p345p111z66p",
            Yaku.ConcealedHand,
            create_default_winning_conditions(
                winning_tile=Tile.P3,
                is_discarded=True,
                seat_wind=Wind.EAST,
            ),
        ),
        (
            "222m333p345p[111z]66p",
            Yaku.SelfDrawn,
            create_default_winning_conditions(
                winning_tile=Tile.P3,
                is_discarded=False,
                seat_wind=Wind.EAST,
            ),
        ),
        (
            "222m333p345p[111z]66p",
            Yaku.RobbingTheKong,
            create_default_winning_conditions(
                winning_tile=Tile.P6,
                is_discarded=True,
                seat_wind=Wind.EAST,
                is_robbing_the_kong=True,
            ),
        ),
        (
            "222m333p345p[111z]66p",
            Yaku.LastTile,
            create_default_winning_conditions(
                winning_tile=Tile.P5,
                is_discarded=True,
                seat_wind=Wind.EAST,
                is_last_tile_of_its_kind=True,
            ),
        ),
        (
            "222m333p345p[1111z]66p",
            Yaku.OutWithReplacementTile,
            create_default_winning_conditions(
                winning_tile=Tile.P6,
                is_discarded=True,
                seat_wind=Wind.EAST,
                is_replacement_tile=True,
            ),
        ),
    ],
)
def test_winning_conditions_yaku(hand_string, expected_yaku, winning_conditions):
    hand = raw_string_to_hand_class(hand_string)
    blocks = divide_general_shape(hand)[0]
    assert (
        expected_yaku in WinningConditionsYakuChecker(blocks, winning_conditions).yakus
    )


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
    print(BlocksYakuChecker([Z11, Z222, Z333, Z4444, M111]).yakus)
    assert (
        Yaku.LittleFourWinds
        in BlocksYakuChecker(
            [Z11, Z222, Z333, Z4444, M111],
        ).yakus
    )
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
    assert (
        Yaku.LittleThreeDragons
        in BlocksYakuChecker(
            [Z555, Z666, Z77, Z111, Z222],
        ).yakus
    )
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
