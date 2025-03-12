from typing import Final

from app.services.score_calculator.enums.enums import Tile
from app.services.score_calculator.hand.hand import Hand

FULLY_HAND_SIZE: Final[int] = 14
KNITTED_CASES: Final[list[set[Tile]]] = [
    {Tile.M1, Tile.M4, Tile.M7, Tile.S2, Tile.S5, Tile.S8, Tile.P3, Tile.P6, Tile.P9},
    {Tile.M1, Tile.M4, Tile.M7, Tile.P2, Tile.P5, Tile.P8, Tile.S3, Tile.S6, Tile.S9},
    {Tile.S1, Tile.S4, Tile.S7, Tile.M2, Tile.M5, Tile.M8, Tile.P3, Tile.P6, Tile.P9},
    {Tile.S1, Tile.S4, Tile.S7, Tile.P2, Tile.P5, Tile.P8, Tile.M3, Tile.M6, Tile.M9},
    {Tile.P1, Tile.P4, Tile.P7, Tile.M2, Tile.M5, Tile.M8, Tile.S3, Tile.S6, Tile.S9},
    {Tile.P1, Tile.P4, Tile.P7, Tile.S2, Tile.S5, Tile.S8, Tile.M3, Tile.M6, Tile.M9},
]


def can_divide_honors_and_knitted_shape(hand: Hand) -> bool:
    if len(hand.call_blocks) or sum(hand.tiles) != FULLY_HAND_SIZE:
        return False

    for case in KNITTED_CASES:
        case_divide_success: bool = True
        for tile in Tile.number_tiles():
            if hand.tiles[tile] if tile not in case else hand.tiles[tile] not in {0, 1}:
                case_divide_success = False
                break
        for tile in Tile.honor_tiles():
            if hand.tiles[tile] not in {0, 1}:
                case_divide_success = False
                break
        if case_divide_success:
            return True
    return False
