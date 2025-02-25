from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand

PAIR_SIZE: Final[int] = 2
FULLY_HAND_SIZE: Final[int] = 14


def divide_seven_pairs_shape(hand: Hand) -> list[Block]:
    parsed_blocks: list[Block] = []

    if len(hand.call_blocks) or sum(hand.tiles) != FULLY_HAND_SIZE:
        return []

    for tile in range(Tile.M1, Tile.F0):
        if hand.tiles[tile] % PAIR_SIZE:
            return []
        for _ in range(hand.tiles[tile] // PAIR_SIZE):
            parsed_blocks.append(
                Block(type=BlockType.PAIR, tile=Tile(tile), is_opened=False),
            )
    return parsed_blocks
