from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType

SIZE: Final[int] = 2


def valid_check_pure_double_chow(blocks: list[Block]) -> bool:
    if len(blocks) != SIZE:
        return False
    return all(block.type == BlockType.SEQUENCE for block in blocks)


def check_pure_double_chow(blocks: list[Block]) -> bool:
    if not valid_check_pure_double_chow(blocks):
        return False
    return blocks[0].tile == blocks[1].tile
