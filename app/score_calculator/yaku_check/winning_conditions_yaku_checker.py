from collections.abc import Callable
from enum import Enum

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Yaku
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions
from app.score_calculator.yaku_check.yaku_checker import YakuChecker


class YakuType(Enum):
    LAST_TILE_OF_GAME = 0
    CONCEALED_STATE = 1
    FOURTH_TILE = 2
    OUT_WITH_REPLACEMENT_TILE = 3


# yaku checker for winning conditions
class HandYakuChecker(YakuChecker):
    def __init__(self, blocks: list[Block], winning_conditions: WinningConditions):
        super().__init__()
        self.blocks: list[Block] = blocks
        self.winning_conditions: WinningConditions = winning_conditions
        self._yakus: list[Yaku]
        self.conditions: dict[YakuType, list[tuple[Callable[[], bool], Yaku]]] = {
            YakuType.LAST_TILE_OF_GAME: self._get_last_tile_of_game_conditions(),
            YakuType.CONCEALED_STATE: self._get_concealed_state_conditions(),
            YakuType.FOURTH_TILE: self._get_fourth_tile_conditions(),
            YakuType.OUT_WITH_REPLACEMENT_TILE: self._get_replacement_tile_conditions(),
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

    def validate_blocks(self, condition: Callable[[Block], bool]) -> bool:
        return all(condition(block) for block in self.blocks)

    def _get_yaku_by_type(self, yaku_type: YakuType) -> Yaku:
        return next(
            (yaku for checker, yaku in self.conditions[yaku_type] if checker()),
            Yaku.ERROR,
        )

    def _get_last_tile_of_game_conditions(
        self,
    ) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: not self.winning_conditions.is_discarded
                and self.winning_conditions.is_last_tile_in_the_game,
                Yaku.LastTileDraw,
            ),
            (
                lambda: self.winning_conditions.is_discarded
                and self.winning_conditions.is_last_tile_in_the_game,
                Yaku.LastTileClaim,
            ),
        ]

    def _get_concealed_state_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: not self.winning_conditions.is_discarded
                and self.validate_blocks(lambda b: not b.is_opened),
                Yaku.FullyConcealedHand,
            ),
            (
                lambda: self.winning_conditions.is_discarded
                and self.validate_blocks(lambda b: not b.is_opened),
                Yaku.ConcealedHand,
            ),
            (
                lambda: not self.winning_conditions.is_discarded
                and not self.validate_blocks(lambda b: not b.is_opened),
                Yaku.SelfDrawn,
            ),
        ]

    def _get_fourth_tile_conditions(self) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.winning_conditions.is_robbing_the_kong,
                Yaku.RobbingTheKong,
            ),
            (
                lambda: self.winning_conditions.is_last_tile_of_its_kind,
                Yaku.LastTile,
            ),
        ]

    def _get_replacement_tile_conditions(
        self,
    ) -> list[tuple[Callable[[], bool], Yaku]]:
        return [
            (
                lambda: self.winning_conditions.is_replacement_tile,
                Yaku.OutWithReplacementTile,
            ),
        ]
