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
        self.conditions: dict[YakuType, list[tuple[bool, Yaku]]] = {
            YakuType.NUM_COMPARE: [
                (self.is_upper_tiles, Yaku.UpperTiles),
                (self.is_middle_tiles, Yaku.MiddleTiles),
                (self.is_lower_tiles, Yaku.LowerTiles),
                (self.is_upper_four, Yaku.UpperFour),
                (self.is_lower_four, Yaku.LowerFour),
            ],
            YakuType.NUM_CONDITION: [
                (self.is_all_honors, Yaku.AllHonors),
                (self.is_all_terminals, Yaku.AllTerminals),
                (self.is_all_terminals_and_honors, Yaku.AllTerminalsAndHonors),
                (self.is_all_simples, Yaku.AllSimples),
                (self.is_no_honor_tiles, Yaku.NoHonorTiles),
            ],
            YakuType.NUM_FLUSH: [
                (self.is_full_flush, Yaku.FullFlush),
                (self.is_half_flush, Yaku.HalfFlush),
                (self.is_one_voided_suit, Yaku.OneVoidedSuit),
            ],
            YakuType.KONG_COUNT: [
                (self.is_four_kongs, Yaku.FourKongs),
                (self.is_three_kongs, Yaku.ThreeKongs),
                (self.is_two_concealed_kongs, Yaku.TwoConcealedKongs),
                (self.is_two_melded_kongs, Yaku.TwoMeldedKongs),
                (self.is_concealed_kong, Yaku.ConcealedKong),
                (self.is_melded_kong, Yaku.MeldedKong),
            ],
            YakuType.CONCEALED_PUNG_COUNT: [
                (self.is_four_concealed_pungs, Yaku.FourConcealedPungs),
                (self.is_three_concealed_pungs, Yaku.ThreeConcealedPungs),
                (self.is_two_concealed_pungs, Yaku.TwoConcealedPungs),
            ],
        }
        self.set_yakus()

    @property
    def yakus(self) -> list[Yaku]:
        return self._yakus

    def set_yakus(self) -> None:
        self._yakus = self.blocks_checker()

    def blocks_checker(self) -> list[Yaku]:
        yakus = [
            next((yaku for checker, yaku in condition if checker), Yaku.ERROR)
            for condition in self.conditions.values()
        ]
        return [yaku for yaku in yakus if yaku != Yaku.ERROR]

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

    # concealed pungs count
    @property
    def is_four_concealed_pungs(self) -> bool:
        return self._count_concealed_pungs() == 4

    @property
    def is_three_concealed_pungs(self) -> bool:
        return self._count_concealed_pungs() == 3

    @property
    def is_two_concealed_pungs(self) -> bool:
        return self._count_concealed_pungs() == 2

    # kong count
    @property
    def is_four_kongs(self) -> bool:
        return self.count_blocks_if(lambda x: x.is_quad) == 4

    @property
    def is_three_kongs(self) -> bool:
        return self.count_blocks_if(lambda x: x.is_quad) == 3

    @property
    def is_two_concealed_kongs(self) -> bool:
        return self.count_blocks_if(lambda x: x.is_quad and not x.is_opened) == 2

    @property
    def is_two_melded_kongs(self) -> bool:
        return self.count_blocks_if(lambda x: x.is_quad) == 2

    @property
    def is_concealed_kong(self) -> bool:
        return self.count_blocks_if(lambda x: x.is_quad and not x.is_opened) == 1

    @property
    def is_melded_kong(self) -> bool:
        return self.count_blocks_if(lambda x: x.is_quad) == 1

    # number flush
    @property
    def is_full_flush(self) -> bool:
        return (
            self.validate_blocks(lambda x: x.is_number)
            and len({block.tile.type for block in self.blocks}) == 1
        )

    @property
    def is_half_flush(self) -> bool:
        return (
            len({block.tile.type for block in self.blocks if block.tile.is_number}) == 1
        )

    @property
    def is_one_voided_suit(self) -> bool:
        return (
            len({block.tile.type for block in self.blocks if block.tile.is_number}) == 2
        )

    # number condition
    @property
    def is_all_honors(self) -> bool:
        return self.validate_tiles(lambda x: x.is_honor)

    @property
    def is_all_terminals(self) -> bool:
        return self.validate_tiles(lambda x: x.is_terminal)

    @property
    def is_all_terminals_and_honors(self) -> bool:
        return self.validate_tiles(lambda x: x.is_terminal or x.is_honor)

    @property
    def is_all_simples(self) -> bool:
        return self.validate_tiles(lambda x: x.is_number and 2 <= x.number <= 8)

    @property
    def is_no_honor_tiles(self) -> bool:
        return self.validate_tiles(lambda x: not x.is_honor)

    # number compare
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
