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
    HAND_SHAPE = 5
    ALL_GREEN = 6
    REVERSIBLE_TILES = 7
    WAIT = 8
    DRAGON_PUNG = 9
    PREVALENT_WIND = 10
    SEAT_WIND = 11


# yaku checker for hand property
class HandYakuChecker(YakuChecker):
    def __init__(self, blocks: list[Block], winning_conditions: WinningConditions):
        super().__init__()
        self.blocks: list[Block] = blocks
        self.winning_conditions: WinningConditions = winning_conditions
        self._yakus: list[Yaku]
        self.conditions: dict[YakuType, list[tuple[Callable[[], bool], Yaku]]] = {
            YakuType.NUM_COMPARE: self._get_num_compare_conditions(),
            YakuType.NUM_CONDITION: self._get_num_condition_conditions(),
            YakuType.NUM_FLUSH: self._get_num_flush_conditions(),
            YakuType.KONG_COUNT: self._get_kong_count_conditions(),
            YakuType.CONCEALED_PUNG_COUNT: self._get_concealed_pung_count_conditions(),
            YakuType.HAND_SHAPE: self._get_hand_shape_conditions(),
            YakuType.ALL_GREEN: self._get_green_tiles_conditions(),
            YakuType.REVERSIBLE_TILES: self._get_reversible_tiles_conditions(),
            YakuType.WAIT: self._get_wait_conditions(),
            YakuType.DRAGON_PUNG: self._get_dragon_pung_conditions(),
            YakuType.PREVALENT_WIND: self._get_prevalent_wind_conditions(),
            YakuType.SEAT_WIND: self._get_seat_wind_conditions(),
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

    def has_constant_gap(self, gap: int) -> bool:
        return all(
            gap == abs(pair[0] - pair[1])
            for pair in zip(self.first_tile_numbers, self.first_tile_numbers[1:])
        )

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
    def first_tile_numbers(self) -> list[int]:
        return sorted(block.tile.number for block in self.blocks)

    @cached_property
    def tiles_by_type(self) -> list[list[int]]:
        return [
            sorted(
                tile.number
                for tile, count in self.tiles.items()
                if tile.type == tile_type
                for _ in range(count)
            )
            for tile_type in {tile.type for tile in self.tiles}
        ]

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

    @cached_property
    def num_tile_types_count(self) -> int:
        return len({b.tile.type for b in self.blocks if b.tile.is_number})

    @cached_property
    def concealed_pungs_count(self) -> int:
        return self.count_blocks_if(
            lambda b: b.is_pung
            and not b.is_opened
            and (
                not self.winning_conditions.is_discarded
                or b.tile != self.winning_conditions.winning_tile
                or self.concealed_tiles[b.tile] - 3 > 0
            ),
        )

    def _get_yaku_by_type(self, yaku_type: YakuType) -> Yaku:
        return next(
            (yaku for checker, yaku in self.conditions[yaku_type] if checker()),
            Yaku.ERROR,
        )

    def _get_num_compare_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.validate_tiles(lambda t: t.is_number and t.number >= 7),
                Yaku.UpperTiles,
            ),
            (
                lambda: self.validate_tiles(
                    lambda x: x.is_number and 4 <= x.number <= 6,
                ),
                Yaku.MiddleTiles,
            ),
            (
                lambda: self.validate_tiles(lambda t: t.is_number and t.number <= 3),
                Yaku.LowerTiles,
            ),
            (
                lambda: self.validate_tiles(lambda t: t.is_number and t.number >= 6),
                Yaku.UpperFour,
            ),
            (
                lambda: self.validate_tiles(lambda t: t.is_number and t.number <= 4),
                Yaku.LowerFour,
            ),
        ]

    def _get_num_condition_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (lambda: self.validate_tiles(lambda t: t.is_honor), Yaku.AllHonors),
            (lambda: self.validate_tiles(lambda t: t.is_terminal), Yaku.AllTerminals),
            (
                lambda: self.validate_tiles(lambda t: t.is_terminal or t.is_honor),
                Yaku.AllTerminalsAndHonors,
            ),
            (
                lambda: self.validate_tiles(
                    lambda t: t.is_number and 2 <= t.number <= 8,
                ),
                Yaku.AllSimples,
            ),
            (lambda: self.validate_tiles(lambda t: not t.is_honor), Yaku.NoHonorTiles),
        ]

    def _get_num_flush_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.validate_blocks(lambda b: b.tile.is_number)
                and self.num_tile_types_count == 1,
                Yaku.FullFlush,
            ),
            (
                lambda: self.num_tile_types_count == 1,
                Yaku.HalfFlush,
            ),
            (
                lambda: self.num_tile_types_count == 2,
                Yaku.OneVoidedSuit,
            ),
        ]

    def _get_kong_count_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (lambda: self.count_blocks_if(lambda b: b.is_quad) == 4, Yaku.FourKongs),
            (lambda: self.count_blocks_if(lambda b: b.is_quad) == 3, Yaku.ThreeKongs),
            (
                lambda: self.count_blocks_if(lambda b: b.is_quad and not b.is_opened)
                == 2,
                Yaku.TwoConcealedKongs,
            ),
            (
                lambda: self.count_blocks_if(lambda b: b.is_quad) == 2,
                Yaku.TwoMeldedKongs,
            ),
            (
                lambda: self.count_blocks_if(lambda b: b.is_quad and not b.is_opened)
                == 1,
                Yaku.ConcealedKong,
            ),
            (lambda: self.count_blocks_if(lambda b: b.is_quad) == 1, Yaku.MeldedKong),
        ]

    def _get_concealed_pung_count_conditions(
        self,
    ) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (lambda: self.concealed_pungs_count == 4, Yaku.FourConcealedPungs),
            (lambda: self.concealed_pungs_count == 3, Yaku.ThreeConcealedPungs),
            (lambda: self.concealed_pungs_count == 2, Yaku.TwoConcealedPungs),
        ]

    def _get_hand_shape_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.validate_tiles(lambda t: t.is_number)
                and self.num_tile_types_count == 1
                and self.count_blocks_if(lambda b: b.type == BlockType.PAIR) == 7
                and self.has_constant_gap(1),
                Yaku.SevenShiftedPairs,
            ),
            (
                lambda: self.validate_tiles(lambda t: t.is_number)
                and self.num_tile_types_count == 1
                and all(
                    self.tiles[t] >= 3 if t.number in {1, 9} else self.tiles[t] >= 1
                    for t in self.tiles
                )
                and self.winning_conditions.count_tenpai_tiles == 9
                and not self.winning_conditions.is_discarded,
                Yaku.NineGates,
            ),
            (
                lambda: len(self.blocks) == 5
                and self.validate_tiles(
                    lambda t: t.is_number
                    and (
                        self.tiles[t] == 2
                        if t.number in {1, 2, 3, 5, 7, 8, 9}
                        else self.tiles[t] == 0
                    ),
                )
                and self.num_tile_types_count == 1,
                Yaku.PureTerminalChows,
            ),
            (
                lambda: len(self.blocks) == 5
                and self.validate_tiles(lambda t: t.is_number and t.number % 2 == 0),
                Yaku.AllEvenPungs,
            ),
            (lambda: len(self.blocks) == 7, Yaku.SevenPairs),
            (
                lambda: len(self.blocks) == 5
                and self.validate_tiles(lambda t: t.is_number)
                and (
                    self.tiles_by_type.count([1, 2, 3, 7, 8, 9]) == 2
                    and self.tiles_by_type.count([5, 5]) == 1
                ),
                Yaku.ThreeSuitedTerminalChows,
            ),
            (lambda: self.count_blocks_if(lambda b: b.is_pung) == 4, Yaku.AllPungs),
            (
                lambda: self.validate_tiles(lambda t: t.is_number)
                and self.count_blocks_if(lambda b: b.is_sequence or b.is_knitted) == 4,
                Yaku.AllChows,
            ),
        ]

    def _get_green_tiles_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        green_tiles = {Tile.S2, Tile.S3, Tile.S4, Tile.S6, Tile.S8, Tile.Z6}
        return [
            (
                lambda: self.validate_tiles(lambda t: t in green_tiles),
                Yaku.AllGreen,
            ),
        ]

    def _get_reversible_tiles_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        reversible_tiles = {
            Tile.P1,
            Tile.P2,
            Tile.P3,
            Tile.P4,
            Tile.P5,
            Tile.P8,
            Tile.P9,
            Tile.S2,
            Tile.S4,
            Tile.S5,
            Tile.S6,
            Tile.S8,
            Tile.S9,
            Tile.Z5,
        }
        return [
            (
                lambda: self.validate_tiles(lambda t: t in reversible_tiles),
                Yaku.ReversibleTiles,
            ),
        ]

    def _get_wait_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.winning_conditions.count_tenpai_tiles == 1
                and any(
                    block.tile.type == self.winning_conditions.winning_tile.type
                    and (
                        (block.tile.number, self.winning_conditions.winning_tile.number)
                        in {(1, 3), (7, 7)}
                    )
                    for block in self.blocks
                    if block.is_sequence and not block.is_opened
                ),
                Yaku.EdgeWait,
            ),
            (
                lambda: self.winning_conditions.count_tenpai_tiles == 1
                and any(
                    block.tile.type == self.winning_conditions.winning_tile.type
                    and block.tile.number + 1
                    == self.winning_conditions.winning_tile.number
                    for block in self.blocks
                    if block.is_sequence and not block.is_opened
                ),
                Yaku.ClosedWait,
            ),
            (
                lambda: self.winning_conditions.count_tenpai_tiles == 1
                and any(
                    block.tile == self.winning_conditions.winning_tile
                    for block in self.blocks
                    if block.is_pair
                ),
                Yaku.SingleWait,
            ),
        ]

    def _get_dragon_pung_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.count_blocks_if(lambda b: b.is_dragon and b.is_pung) == 1,
                Yaku.DragonPung,
            ),
        ]

    def _get_prevalent_wind_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        for b in self.blocks:
            print(
                b.tile,
                self.winning_conditions.round_wind,
                int(b.tile) == int(self.winning_conditions.round_wind),
            )
        return [
            (
                lambda: self.count_blocks_if(
                    lambda b: b.is_pung
                    and int(b.tile) == self.winning_conditions.round_wind,
                )
                == 1,
                Yaku.PrevalentWind,
            ),
        ]

    def _get_seat_wind_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.count_blocks_if(
                    lambda b: b.is_pung
                    and int(b.tile) == self.winning_conditions.seat_wind,
                )
                == 1,
                Yaku.SeatWind,
            ),
        ]
