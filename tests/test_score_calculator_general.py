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
    ],
)
def test_tenpai_tiles_checker(hand_string, yaku_score_list, winning_conditions):
    hand = raw_string_to_hand_class(hand_string)
    sc = ScoreCalculator(hand, winning_conditions=winning_conditions)
    sc.general_shape_calculator()
    print(sc.highest_result.yaku_score_list)
    assert set(sc.highest_result.yaku_score_list) == set(yaku_score_list)
