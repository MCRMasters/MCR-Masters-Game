from app.score_calculator.block.block import Block


def has_opened_blocks(blocks: list[Block]) -> bool:
    return any(block.is_opened for block in blocks)
