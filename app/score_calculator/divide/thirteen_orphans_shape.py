from typing import Final

from app.score_calculator.enums.enums import Tile
from app.score_calculator.hand.hand import Hand

FULLY_HAND_SIZE: Final[int] = 14


def can_divide_thirteen_orphans_shape(hand: Hand) -> bool:
    if len(hand.call_blocks) or sum(hand.tiles) != FULLY_HAND_SIZE:
        return False

    for tile in range(Tile.M1, Tile.F0):
        if Tile(tile).is_outside and hand.tiles[tile] < 1:
            return False
    return True
