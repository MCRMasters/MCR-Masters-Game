from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import batched

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Tile


@dataclass
class Hand:
    """A hand of tiles and call blocks.

    Attributes:
        tiles (List[int]): A list representing the count of each tile in the hand.
        call_blocks (list[Block]): A list of Block objects representing call blocks.
    """

    tiles: list[int]
    call_blocks: list[Block]

    @staticmethod
    def create_from_tiles(tiles: list[Tile], call_blocks: list[Block]) -> Hand:
        _tiles = [0] * 34
        for tile_index in tiles:
            _tiles[tile_index] += 1
        return Hand(tiles=_tiles, call_blocks=deepcopy(call_blocks))

    def __repr__(self) -> str:
        """Return a string representation of the Hand.

        Tiles are displayed in rows of 9 (e.g., 1-9 manzu, 1-9 pinzu, etc.),
        with each row separated by a newline. The call blocks are then printed
        on a new line.

        Returns:
            str: A string representation of the Hand.
        """
        tiles_rep = "[tiles]\n"
        tiles_rep += "\n".join(
            " ".join(map(str, batch)) for batch in batched(self.tiles, 9)
        )
        tiles_rep += f"\ncall_blocks: {self.call_blocks}"
        return tiles_rep
