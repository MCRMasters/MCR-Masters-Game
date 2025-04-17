from typing import Final

from app.services.score_calculator.enums.enums import Tile
from app.services.score_calculator.hand.hand import Hand

FULLY_HAND_SIZE: Final[int] = 14


def can_divide_thirteen_orphans_shape(hand: Hand) -> bool:
    if len(hand.call_blocks) or sum(hand.tiles) != FULLY_HAND_SIZE:
        return False

    return all(
        hand.tiles[tile] >= 1 if Tile(tile).is_outside else hand.tiles[tile] == 0
        for tile in Tile.all_tiles()
    )
