import logging
from copy import deepcopy
from typing import Final

from app.services.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.services.score_calculator.divide.honors_and_knitted_shape import (
    can_divide_honors_and_knitted_shape,
)
from app.services.score_calculator.divide.seven_pairs_shape import (
    divide_seven_pairs_shape,
)
from app.services.score_calculator.divide.thirteen_orphans_shape import (
    can_divide_thirteen_orphans_shape,
)
from app.services.score_calculator.enums.enums import BlockType, Tile
from app.services.score_calculator.hand.hand import Hand

TENPAI_HAND_SIZE: Final[int] = 13


logger = logging.getLogger(__name__)


def get_tenpai_tiles(tenpai_hand: Hand) -> list[Tile]:
    if any(not 0 <= tiles_count <= 4 for tiles_count in tenpai_hand.tiles):
        logger.debug(f"{tenpai_hand}")
        raise ValueError("Wrong tenpai hand")
    total_tiles_count: int = sum(tenpai_hand.tiles)
    for block in tenpai_hand.call_blocks:
        total_tiles_count -= 1 if block.type == BlockType.QUAD else 0
    if total_tiles_count != TENPAI_HAND_SIZE:
        raise ValueError("Wrong tenpai hand size.")

    tenpai_tiles: list[Tile] = []

    for tile in Tile.all_tiles():
        hand = deepcopy(tenpai_hand)
        hand.tiles[tile] += 1
        if (
            divide_general_shape(hand)
            or divide_general_shape_knitted_sub(hand)
            or divide_seven_pairs_shape(hand)
            or can_divide_thirteen_orphans_shape(hand)
            or can_divide_honors_and_knitted_shape(hand)
        ):
            tenpai_tiles.append(Tile(tile))
    return tenpai_tiles
