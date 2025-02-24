from app.score_calculator.block.block import Block


class Hand:
    """Represents a hand consisting of tiles and call blocks.

    This class stores a list of tiles in hand and a list of call blocks.

    Attributes:
        tiles (List[int]): A list representing the count of each tile in the hand.
        call_blocks (List[Block]): A list of Block objects representing the call blocks.
    """

    def __init__(self, tiles: list[int], call_blocks: list[Block]):
        """Initializes a Hand object.

        Args:
            tiles (List[int]): A list of integers representing the tile counts.
            call_blocks (List[Block]): A list of Block objects.
        """
        self.tiles = tiles
        self.call_blocks = call_blocks

    def __repr__(self) -> str:
        """Returns a string representation of the Hand.

        The tiles are printed in rows of 9 tiles each followed by a blank line,
        and the call blocks are printed afterwards.

        Returns:
            str: The string representation of the Hand.
        """
        rep = "[tiles]\n"
        for i, tile in enumerate(self.tiles):
            rep += f"{tile} "
            if (i + 1) % 9 == 0:
                rep += "\n"
        rep += "\n"
        rep += f"call_blocks: {self.call_blocks}"
        return rep
