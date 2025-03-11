import pytest

from app.score_calculator.enums.enums import Tile, Wind, Yaku
from app.score_calculator.score_calculator import ScoreCalculator
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions
from tests.test_utils import raw_string_to_hand_class


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
    "hand_string, yaku_score_list, winning_conditions",
    [
        (
            "66m111222333444z",
            [
                (Yaku.BigFourWinds, 88),
                (Yaku.FourConcealedPungs, 64),
                (Yaku.HalfFlush, 6),
                (Yaku.SingleWait, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.M6, is_discarded=True),
        ),
        (
            "11999m111p111999s",
            [
                (Yaku.FourConcealedPungs, 64),
                (Yaku.AllTerminals, 64),
                (Yaku.DoublePung, 4),
                (Yaku.SingleWait, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.M1, is_discarded=True),
        ),
        (
            "12223456567789p",
            [
                (Yaku.FullFlush, 24),
                (Yaku.PureStraight, 16),
                (Yaku.ConcealedHand, 2),
                (Yaku.AllChows, 2),
                (Yaku.ClosedWait, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.P2, is_discarded=True),
        ),
        (
            "123m234s345p456m77z",
            [
                (Yaku.MixedShiftedChows, 6),
                (Yaku.ConcealedHand, 2),
                (Yaku.ShortStraight, 1),
                (Yaku.SingleWait, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.Z7, is_discarded=True),
        ),
        (
            "19m19s19p12345677z",
            [
                (Yaku.ThirteenOrphans, 88),
                (Yaku.FullyConcealedHand, 4),
            ],
            create_default_winning_conditions(winning_tile=Tile.P1, is_discarded=False),
        ),
        (
            "19m19s19p12345677z",
            [
                (Yaku.ThirteenOrphans, 88),
                (Yaku.FullyConcealedHand, 4),
            ],
            create_default_winning_conditions(winning_tile=Tile.P1, is_discarded=False),
        ),
        (
            "[234s]147m258s36999p",
            [
                (Yaku.KnittedStraight, 12),
                (Yaku.AllChows, 2),
                (Yaku.SelfDrawn, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.P9, is_discarded=False),
        ),
        (
            "[234s]147m258s369p11z",
            [
                (Yaku.KnittedStraight, 12),
                (Yaku.SingleWait, 1),
                (Yaku.SelfDrawn, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.Z1, is_discarded=False),
        ),
        (
            "147m258p369s12345z",
            [
                (Yaku.KnittedStraight, 12),
                (Yaku.LesserHonorsAndKnittedTiles, 12),
                (Yaku.FullyConcealedHand, 4),
            ],
            create_default_winning_conditions(winning_tile=Tile.Z1, is_discarded=False),
        ),
        (
            "[4444m][5555m][2222s]222p66p",
            [
                (Yaku.ThreeKongs, 32),
                (Yaku.AllPungs, 6),
                (Yaku.AllSimples, 2),
                (Yaku.DoublePung, 2),
                (Yaku.SingleWait, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.P6, is_discarded=True),
        ),
        (
            "345678m67888p45s3s",
            [
                (Yaku.FullyConcealedHand, 4),
                (Yaku.AllChows, 2),
                (Yaku.AllSimples, 2),
                (Yaku.MixedDoubleChow, 2),
                (Yaku.ShortStraight, 1),
            ],
            create_default_winning_conditions(winning_tile=Tile.S3, is_discarded=False),
        ),
    ],
)
def test_score_checker(hand_string, yaku_score_list, winning_conditions):
    hand = raw_string_to_hand_class(hand_string)
    sc = ScoreCalculator(hand=hand, winning_conditions=winning_conditions)
    print(sc._highest_result.yaku_score_list)
    print(hand)
    assert set(sc._highest_result.yaku_score_list) == set(yaku_score_list)
