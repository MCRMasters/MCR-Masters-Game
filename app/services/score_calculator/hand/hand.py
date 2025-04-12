from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import batched

from app.services.game_manager.models.enums import GameTile
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.types import CallBlockType
from app.services.score_calculator.block.block import Block
from app.services.score_calculator.enums.enums import Tile


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
        _tiles = [0] * 35
        for tile_index in tiles:
            _tiles[tile_index] += 1
        return Hand(tiles=_tiles, call_blocks=deepcopy(call_blocks))

    @staticmethod
    def create_from_game_hand(hand: GameHand) -> Hand:
        _tiles = [0] * 35
        _call_blocks = []
        for tile in hand.tiles:
            if not GameTile(tile).is_flower:
                _tiles[tile] += hand.tiles[tile]
            else:
                _tiles[Tile.F0] += hand.tiles[tile]
        for call_block in hand.call_blocks:
            _call_blocks.append(Block.create_from_call_block(call_block))
            match call_block.type:
                case CallBlockType.CHII:
                    for i in range(3):
                        _tiles[call_block.first_tile + i] += 1
                case CallBlockType.PUNG:
                    _tiles[call_block.first_tile] += 3
                case (
                    CallBlockType.AN_KONG
                    | CallBlockType.SHOMIN_KONG
                    | CallBlockType.DAIMIN_KONG
                ):
                    _tiles[call_block.first_tile] += 4
        return Hand(tiles=_tiles, call_blocks=_call_blocks)

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
