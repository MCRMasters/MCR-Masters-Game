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
    def __init__(self, block_type: BlockType, tile: int, source: BlockSource = BlockSource.SELF, source_tile_index: int = 0):
        self.type = block_type
        self.tile = tile
        self.source = source
        self.source_tile_index = source_tile_index

    def __repr__(self):
        return (f"Block(type={self.type.name}, tile={self.tile}, "
                f"source={self.source.name}, source_tile_index={self.source_tile_index})")
