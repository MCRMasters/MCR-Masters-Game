from dataclasses import dataclass

from app.score_calculator.enums.enums import BlockType, Tile


@dataclass
class Block:
    """Represents a block of tiles.

    The `tile` attribute refers to the first tile of the block.
    For example:
        789m -> 7m,
        999p -> 9p,
        147s -> 1s.

    Attributes:
        type (BlockType): The type of block (e.g., sequence, triplet, etc.).
        tile (int): The first tile of the block.
        is_opened (bool): open state of the block (default is False(Closed block)).
    """

    type: BlockType
    tile: Tile
    is_opened: bool = False
