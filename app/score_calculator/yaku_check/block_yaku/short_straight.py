from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType

BLOCKS_SIZE: Final[int] = 2
SHORT_STRAIGHT_GAP: Final[int] = 3


def valid_check_short_straight(blocks: list[Block]) -> bool:
    return len(blocks) == BLOCKS_SIZE and all(
        block.type == BlockType.SEQUENCE for block in blocks
    )


def check_short_straight(blocks: list[Block]) -> bool:
    if not valid_check_short_straight(blocks):
        return False
    return (
        len({block.tile.get_type() for block in blocks}) == 1
        and abs(blocks[0].tile - blocks[1].tile) == SHORT_STRAIGHT_GAP
    )
