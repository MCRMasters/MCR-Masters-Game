# block.py
from enum import Enum

class BlockType(Enum):
    SEQUENCE = 0
    TRIPLET = 1
    QUAD = 2
    PAIR = 3
    KNITTED = 4
    SINGLETILE = 5

class BlockSource(Enum):
    SELF = 0
    SHIMOCHA = 1
    TOIMEN = 2
    KAMICHA = 3

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
        source (BlockSource): The source of the block (default is BlockSource.SELF).
    """

    def __init__(self, block_type: BlockType, tile: int, source: BlockSource = BlockSource.SELF, source_tile_index: int = 0):
        self.type = block_type
        self.tile = tile
        self.source = source

    def __repr__(self):
        return (f"Block(type={self.type.name}, tile={self.tile}, "
                f"source={self.source.name})")
