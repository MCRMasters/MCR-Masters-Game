# hand.py
from dataclasses import dataclass

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Tile


@dataclass
class Hand:
    """A hand of tiles and call blocks.

    Attributes:
        tiles (list[Tile]): A list representing the tiles in the hand.
        call_blocks (list[Block]): A list of Block objects representing call blocks.
    """

    tiles: list[Tile]
    call_blocks: list[Block]

    def __repr__(self) -> str:
        """Return a string representation of the Hand.

        Tiles are displayed in rows of 9, with each row separated by a newline.
        The call blocks are then printed on a new line.

        Returns:
            str: A string representation of the Hand.
        """
        tiles_rep = "[tiles]\n"
        for i, tile in enumerate(self.tiles):
            tiles_rep += f"{tile} "
            if (i + 1) % 9 == 0:
                tiles_rep += "\n"
        tiles_rep += "\n"
        tiles_rep += f"call_blocks: {self.call_blocks}"
        return tiles_rep
