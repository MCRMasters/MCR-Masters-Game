from collections import defaultdict
from collections.abc import Callable
from functools import cached_property

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.score_calculator.yaku_check.yaku_checker import YakuChecker


# yaku checker for hand property
class HandYakuChecker(YakuChecker):
    def __init__(self, blocks: list[Block]):
        super().__init__()
        self.blocks: list[Block] = blocks
        self._yakus: list[Yaku]
        self.conditions: dict[str, list[tuple[bool, Yaku]]] = {
            "num_compair": [
                (self.is_upper_tiles, Yaku.UpperTiles),
                (self.is_middle_tiles, Yaku.MiddleTiles),
                (self.is_lower_tiles, Yaku.LowerTiles),
                (self.is_upper_four, Yaku.UpperFour),
                (self.is_lower_four, Yaku.LowerFour),
            ],
        }
        self.set_yakus()

    @property
    def yakus(self) -> list[Yaku]:
        return self._yakus

    def set_yakus(self) -> None:
        self._yakus = self.blocks_checker()

    def blocks_checker(self) -> list[Yaku]:
        return list(
            filter(
                lambda x: x != Yaku.ERROR,
                (
                    next((yaku for checker, yaku in condition if checker), Yaku.ERROR)
                    for condition in self.conditions.values()
                ),
            ),
        )

    # utils
    def validate_blocks(self, condition: Callable[[Block], bool]) -> bool:
        return all(condition(block) for block in self.blocks)

    def validate_tiles(self, condition: Callable[[Tile], bool]) -> bool:
        return all(condition(tile) for tile in self.tiles)

    def count_blocks_if(self, condition: Callable[[Block], bool]) -> int:
        return sum(1 for block in self.blocks if condition(block))

    @cached_property
    def tiles(self) -> defaultdict[Tile, int]:
        _tiles: defaultdict[Tile, int] = defaultdict(int)
        for block in self.blocks:
            match block.type:
                case BlockType.PAIR:
                    _tiles[block.tile] += 2
                case BlockType.TRIPLET:
                    _tiles[block.tile] += 3
                case BlockType.QUAD:
                    _tiles[block.tile] += 4
                case BlockType.SEQUENCE:
                    for i in range(3):
                        _tiles[block.tile + i] += 1
                case BlockType.KNITTED:
                    for i in range(3):
                        _tiles[block.tile + i * 3] += 1
        return _tiles

    @property
    def is_upper_tiles(self) -> bool:
        return self.validate_tiles(lambda x: x.is_number and x.number >= 7)

    @property
    def is_middle_tiles(self) -> bool:
        return self.validate_tiles(lambda x: x.is_number and 4 <= x.number <= 6)

    @property
    def is_lower_tiles(self) -> bool:
        return self.validate_tiles(lambda x: x.is_number and x.number <= 3)

    @property
    def is_upper_four(self) -> bool:
        return self.validate_tiles(lambda x: x.is_number and x.number >= 6)

    @property
    def is_lower_four(self) -> bool:
        return self.validate_tiles(lambda x: x.is_number and x.number <= 4)
