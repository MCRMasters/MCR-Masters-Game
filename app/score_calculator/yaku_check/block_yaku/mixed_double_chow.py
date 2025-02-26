from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType

BLOCKS_SIZE: Final[int] = 2
TILE_TYPE_COUNT: Final[int] = 2


def valid_check_mixed_double_chow(blocks: list[Block]) -> bool:
    return len(blocks) == BLOCKS_SIZE and all(
        block.type == BlockType.SEQUENCE for block in blocks
    )


def check_mixed_double_chow(blocks: list[Block]) -> bool:
    if not valid_check_mixed_double_chow(blocks):
        return False
    return (
        len({block.tile.get_type() for block in blocks}) == TILE_TYPE_COUNT
        and blocks[0].tile.get_number() == blocks[1].tile.get_number()
    )
