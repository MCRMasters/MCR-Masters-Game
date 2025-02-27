from dataclasses import dataclass
from typing import Final

from app.score_calculator.enums.enums import BlockType, Tile

SEQUENCE_SIZE: Final[int] = 3
KNITTED_SIZE: Final[int] = 3
KNITTED_GAP: Final[int] = 3
FIVE: Final[int] = 5


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

    @property
    def is_sequence(self) -> bool:
        return self.type == BlockType.SEQUENCE

    @property
    def is_triplet(self) -> bool:
        return self.type in {BlockType.TRIPLET, BlockType.QUAD}

    @property
    def is_quad(self) -> bool:
        return self.type == BlockType.QUAD

    @property
    def is_pair(self) -> bool:
        return self.type == BlockType.PAIR

    @property
    def is_number(self) -> bool:
        return self.tile.is_number

    @property
    def is_honor(self) -> bool:
        return self.tile.is_honor

    @property
    def is_manzu(self) -> bool:
        return self.tile.is_manzu

    @property
    def is_pinzu(self) -> bool:
        return self.tile.is_pinzu

    @property
    def is_souzu(self) -> bool:
        return self.tile.is_souzu

    @property
    def is_wind(self) -> bool:
        return self.tile.is_wind

    @property
    def is_dragon(self) -> bool:
        return self.tile.is_dragon

    @property
    def is_terminal(self) -> bool:
        return all(tile.is_terminal for tile in self.tiles)

    @property
    def is_outside(self) -> bool:
        return self.is_honor or self.is_terminal

    @property
    def has_outside(self) -> bool:
        return any(tile.is_outside for tile in self.tiles)

    @property
    def has_five(self) -> bool:
        return any(tile.number == FIVE for tile in self.tiles)

    @property
    def tiles(self) -> list[Tile]:
        tiles: list[Tile] = []
        if self.type == BlockType.SEQUENCE:
            tiles = [self.tile + i for i in range(SEQUENCE_SIZE)]
        elif self.type == BlockType.KNITTED:
            tiles = [self.tile + i for i in range(0, KNITTED_SIZE, KNITTED_GAP)]
        else:
            tiles = [self.tile]
        return tiles
