from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from functools import cached_property

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions
from app.score_calculator.yaku_check.yaku_checker import YakuChecker


class YakuType(Enum):
    NUM_COMPARE = 0
    NUM_CONDITION = 1
    NUM_FLUSH = 2
    KONG_COUNT = 3
    CONCEALED_PUNG_COUNT = 4


# yaku checker for hand property
class HandYakuChecker(YakuChecker):
    def __init__(self, blocks: list[Block], winning_conditions: WinningConditions):
        super().__init__()
        self.blocks: list[Block] = blocks
        self.winning_conditions: WinningConditions = winning_conditions
        self._yakus: list[Yaku]
        self.conditions: dict[YakuType, list[tuple[Callable[[], bool], Yaku]]] = {
            YakuType.NUM_COMPARE: [
                (
                    lambda: self.validate_tiles(
                        lambda x: x.is_number and x.number >= 7,
                    ),
                    Yaku.UpperTiles,
                ),
                (
                    lambda: self.validate_tiles(
                        lambda x: x.is_number and 4 <= x.number <= 6,
                    ),
                    Yaku.MiddleTiles,
                ),
                (
                    lambda: self.validate_tiles(
                        lambda x: x.is_number and x.number <= 3,
                    ),
                    Yaku.LowerTiles,
                ),
                (
                    lambda: self.validate_tiles(
                        lambda x: x.is_number and x.number >= 6,
                    ),
                    Yaku.UpperFour,
                ),
                (
                    lambda: self.validate_tiles(
                        lambda x: x.is_number and x.number <= 4,
                    ),
                    Yaku.LowerFour,
                ),
            ],
            YakuType.NUM_CONDITION: [
                (lambda: self.validate_tiles(lambda x: x.is_honor), Yaku.AllHonors),
                (
                    lambda: self.validate_tiles(lambda x: x.is_terminal),
                    Yaku.AllTerminals,
                ),
                (
                    lambda: self.validate_tiles(lambda x: x.is_terminal or x.is_honor),
                    Yaku.AllTerminalsAndHonors,
                ),
                (
                    lambda: self.validate_tiles(
                        lambda x: x.is_number and 2 <= x.number <= 8,
                    ),
                    Yaku.AllSimples,
                ),
                (
                    lambda: self.validate_tiles(lambda x: not x.is_honor),
                    Yaku.NoHonorTiles,
                ),
            ],
            YakuType.NUM_FLUSH: [
                (
                    lambda: self.validate_blocks(lambda b: b.tile.is_number)
                    and len({b.tile.type for b in self.blocks}) == 1,
                    Yaku.FullFlush,
                ),
                (
                    lambda: len({b.tile.type for b in self.blocks if b.tile.is_number})
                    == 1,
                    Yaku.HalfFlush,
                ),
                (
                    lambda: len({b.tile.type for b in self.blocks if b.tile.is_number})
                    == 2,
                    Yaku.OneVoidedSuit,
                ),
            ],
            YakuType.KONG_COUNT: [
                (
                    lambda: self.count_blocks_if(lambda b: b.is_quad) == 4,
                    Yaku.FourKongs,
                ),
                (
                    lambda: self.count_blocks_if(lambda b: b.is_quad) == 3,
                    Yaku.ThreeKongs,
                ),
                (
                    lambda: self.count_blocks_if(
                        lambda b: b.is_quad and not b.is_opened,
                    )
                    == 2,
                    Yaku.TwoConcealedKongs,
                ),
                (
                    lambda: self.count_blocks_if(lambda b: b.is_quad) == 2,
                    Yaku.TwoMeldedKongs,
                ),
                (
                    lambda: self.count_blocks_if(
                        lambda b: b.is_quad and not b.is_opened,
                    )
                    == 1,
                    Yaku.ConcealedKong,
                ),
                (
                    lambda: self.count_blocks_if(lambda b: b.is_quad) == 1,
                    Yaku.MeldedKong,
                ),
            ],
            YakuType.CONCEALED_PUNG_COUNT: [
                (lambda: self._count_concealed_pungs() == 4, Yaku.FourConcealedPungs),
                (lambda: self._count_concealed_pungs() == 3, Yaku.ThreeConcealedPungs),
                (lambda: self._count_concealed_pungs() == 2, Yaku.TwoConcealedPungs),
            ],
        }
        self.set_yakus()

    @property
    def yakus(self) -> list[Yaku]:
        return self._yakus

    def set_yakus(self) -> None:
        self._yakus = self.blocks_checker()

    def blocks_checker(self) -> list[Yaku]:
        return [
            self._get_yaku_by_type(yaku_type)
            for yaku_type in YakuType
            if self._get_yaku_by_type(yaku_type) != Yaku.ERROR
        ]

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

    @cached_property
    def concealed_tiles(self) -> defaultdict[Tile, int]:
        _concealed_tiles: defaultdict[Tile, int] = defaultdict(int)
        for block in self.blocks:
            if block.is_opened:
                continue
            match block.type:
                case BlockType.PAIR:
                    _concealed_tiles[block.tile] += 2
                case BlockType.TRIPLET:
                    _concealed_tiles[block.tile] += 3
                case BlockType.QUAD:
                    _concealed_tiles[block.tile] += 4
                case BlockType.SEQUENCE:
                    for i in range(3):
                        _concealed_tiles[block.tile + i] += 1
                case BlockType.KNITTED:
                    for i in range(3):
                        _concealed_tiles[block.tile + i * 3] += 1
        return _concealed_tiles

    # general yaku checker
    def _count_concealed_pungs(self) -> int:
        return self.count_blocks_if(
            lambda x: x.is_pung
            and not x.is_opened
            and (
                not self.winning_conditions.is_discarded
                or x.tile != self.winning_conditions.winning_tile
                or self.concealed_tiles[x.tile] - 3 > 0
            ),
        )

    def _get_yaku_by_type(self, yaku_type: YakuType) -> Yaku:
        return next(
            (yaku for checker, yaku in self.conditions[yaku_type] if checker()),
            Yaku.ERROR,
        )

    def get_num_compare_yaku(self) -> Yaku:
        return self._get_yaku_by_type(YakuType.NUM_COMPARE)

    def get_num_condition_yaku(self) -> Yaku:
        return self._get_yaku_by_type(YakuType.NUM_CONDITION)

    def get_num_flush_yaku(self) -> Yaku:
        return self._get_yaku_by_type(YakuType.NUM_FLUSH)

    def get_kong_count_yaku(self) -> Yaku:
        return self._get_yaku_by_type(YakuType.KONG_COUNT)

    def get_concealed_pung_count_yaku(self) -> Yaku:
        return self._get_yaku_by_type(YakuType.CONCEALED_PUNG_COUNT)
