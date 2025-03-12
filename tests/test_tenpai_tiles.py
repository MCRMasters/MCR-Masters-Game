import pytest

from app.services.score_calculator.enums.enums import Tile
from app.services.score_calculator.tenpai_calculator import get_tenpai_tiles
from tests.test_utils import raw_string_to_hand_class


@pytest.mark.parametrize(
    "hand_string, tenpai_tiles",
    [
        ("123m123s111p222p3p", [Tile.P1, Tile.P2, Tile.P3, Tile.P4]),
        ("2233344556677s", [Tile.S2, Tile.S3, Tile.S4, Tile.S7]),
        ("19s19p19m1234577z", [Tile.Z6]),
        ("147m258p36s12345z", [Tile.S9, Tile.Z6, Tile.Z7]),
    ],
)
def test_tenpai_tiles_checker(hand_string, tenpai_tiles):
    hand = raw_string_to_hand_class(hand_string)
    assert sorted(get_tenpai_tiles(tenpai_hand=hand)) == tenpai_tiles
