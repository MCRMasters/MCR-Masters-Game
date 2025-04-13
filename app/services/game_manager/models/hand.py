from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from typing import ClassVar, Final

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.call_block import CallBlock
from app.services.game_manager.models.enums import GameTile, RelativeSeat
from app.services.game_manager.models.types import (
    ActionType,
    CallBlockType,
    GameEventType,
)
from app.services.game_manager.models.winning_conditions import GameWinningConditions


@dataclass
class GameHand:
    tiles: Counter[GameTile]
    call_blocks: list[CallBlock]
    tsumo_tile: GameTile | None = None
    flower_point: int = 0

    FULL_HAND_SIZE: Final[int] = 14
    FLOWER_TILES: ClassVar[Counter[GameTile]] = Counter(
        map(GameTile, GameTile.flower_tiles()),
    )

    @staticmethod
    def create_from_tiles(tiles: list[GameTile]) -> GameHand:
        return GameHand(
            tiles=Counter(tiles),
            call_blocks=[],
            tsumo_tile=None,
        )

    @property
    def has_flower(self) -> bool:
        return bool(self.FLOWER_TILES & self.tiles)

    def apply_flower(self) -> GameTile | None:
        if not (self.FLOWER_TILES & self.tiles):
            raise ValueError("Cannot apply flower: hand doesn't have flower tile")
        self.flower_point += 1
        applied_tile: GameTile | None = None
        if self.tsumo_tile and GameTile(self.tsumo_tile).is_flower:
            applied_tile = self.tsumo_tile
            self.apply_discard(applied_tile)
            return applied_tile
        else:
            for flower_tile in GameTile.flower_tiles():
                if flower_tile in self.tiles:
                    applied_tile = GameTile(flower_tile)
                    self.apply_discard(applied_tile)
                    break
            return applied_tile

    @property
    def hand_size(self) -> int:
        return sum(self.tiles.values()) + len(self.call_blocks) * 3

    def apply_init_flower_tsumo(self, tile: GameTile) -> GameTile:
        if self.hand_size >= GameHand.FULL_HAND_SIZE:
            raise ValueError("Cannot apply tsumo: hand is already full.")
        self.tiles[tile] += 1
        if self.hand_size == GameHand.FULL_HAND_SIZE:
            self.tsumo_tile = tile
        return tile

    def apply_tsumo(self, tile: GameTile) -> GameTile:
        if self.hand_size >= GameHand.FULL_HAND_SIZE:
            raise ValueError("Cannot apply tsumo: hand is already full.")
        self.tiles[tile] += 1
        self.tsumo_tile = tile
        return tile

    def get_rightmost_tile(self) -> GameTile | None:
        if self.tsumo_tile:
            return self.tsumo_tile
        if not self.tiles:
            return None
        return sorted(self.tiles.keys())[-1]

    def apply_discard(self, tile: GameTile) -> None:
        if tile not in self.tiles:
            raise ValueError(f"Cannot apply discard: hand doesn't have tile {tile}")
        self._remove_tiles(tile, 1)
        self.tsumo_tile = None

    def apply_call(self, block: CallBlock) -> None:
        match block.type:
            case CallBlockType.CHII:
                self._apply_chii(block=block)
            case CallBlockType.PUNG:
                self._apply_pung(block=block)
            case CallBlockType.AN_KONG:
                self._apply_an_kong(block=block)
            case CallBlockType.DAIMIN_KONG:
                self._apply_daimin_kong(block=block)
            case CallBlockType.SHOMIN_KONG:
                self._apply_shomin_kong(block=block)

    def _remove_tiles(self, tile: GameTile, count: int) -> None:
        self.tiles[tile] -= count
        if self.tiles[tile] == 0:
            del self.tiles[tile]

    def get_possible_chii_actions(
        self,
        priority: RelativeSeat,
        winning_condition: GameWinningConditions,
    ) -> list[Action]:
        result: list[Action] = []
        if winning_condition.winning_tile is None:
            raise ValueError(
                "[GameHand.get_possible_chii_actions]tile is none",
            )
        tile: GameTile = winning_condition.winning_tile
        if winning_condition.is_last_tile_in_the_game or not GameTile(tile).is_number:
            return result
        for delta in [-2, -1, 0]:
            chii_tile_list: list[GameTile] = [
                GameTile(new_tile)
                for index in range(3)
                if (raw_tile := tile + delta + index) in GameTile
                and (new_tile := GameTile(raw_tile)).type == GameTile(tile).type
                and new_tile in self.tiles
                and new_tile != tile
            ]
            if len(chii_tile_list) == 2:
                result.append(
                    Action(
                        type=ActionType.CHII,
                        seat_priority=priority,
                        tile=GameTile(tile + delta),
                    ),
                )
        return result

    def get_possible_pon_actions(
        self,
        priority: RelativeSeat,
        winning_condition: GameWinningConditions,
    ) -> list[Action]:
        result: list[Action] = []
        if winning_condition.winning_tile is None:
            raise ValueError(
                "[GameHand.get_possible_pon_actions]tile is none",
            )
        tile: GameTile = winning_condition.winning_tile
        if (
            self.tiles.get(tile, 0) >= 2
            and not winning_condition.is_last_tile_in_the_game
            and winning_condition.is_discarded
        ):
            result.append(
                Action(type=ActionType.PON, seat_priority=priority, tile=tile),
            )
        return result

    def get_kan_event_type_from_tile(
        self,
        tile: GameTile,
        is_discarded: bool,
    ) -> GameEventType | None:
        result: GameEventType | None = None
        if is_discarded:
            if self.tiles.get(tile, 0) >= 3:
                result = GameEventType.DAIMIN_KAN
        else:
            if self.tiles.get(tile, 0) == 4:
                result = GameEventType.AN_KAN
            for block in self.call_blocks:
                if block.type == CallBlockType.PUNG and (block.first_tile == tile):
                    result = GameEventType.SHOMIN_KAN
                    break
        return result

    def get_possible_kan_actions(
        self,
        priority: RelativeSeat,
        winning_condition: GameWinningConditions,
    ) -> list[Action]:
        result: list[Action] = []
        if winning_condition.winning_tile is None:
            raise ValueError(
                "[GameHand.get_possible_kan_actions]tile is none",
            )
        tile: GameTile = winning_condition.winning_tile
        if winning_condition.is_last_tile_in_the_game:
            return result
        # 대명깡
        if winning_condition.is_discarded:
            if self.tiles.get(tile, 0) >= 3:
                result.append(
                    Action(type=ActionType.KAN, seat_priority=priority, tile=tile),
                )
        else:
            # 안깡
            for an_kan_tile, count in self.tiles.items():
                if count == 4:
                    result.append(
                        Action(
                            type=ActionType.KAN,
                            seat_priority=priority,
                            tile=an_kan_tile,
                        ),
                    )
            # 소명깡
            for block in self.call_blocks:
                if block.type == CallBlockType.PUNG and (
                    block.first_tile == tile or block.first_tile in self.tiles
                ):
                    result.append(
                        Action(
                            type=ActionType.KAN,
                            seat_priority=priority,
                            tile=block.first_tile,
                        ),
                    )
        return result

    def _apply_chii(self, block: CallBlock) -> None:
        delete_tile_list: list[GameTile] = [
            GameTile(block.first_tile + index)
            for index in range(3)
            if index != block.source_tile_index
        ]
        if not all(tile in self.tiles for tile in delete_tile_list):
            raise ValueError(
                "Cannot apply chii: not enough valid tiles to chii",
            )
        for delete_tile in delete_tile_list:
            self._remove_tiles(delete_tile, 1)
        self.call_blocks.append(deepcopy(block))

    def _apply_pung(self, block: CallBlock) -> None:
        if self.tiles.get(block.first_tile, 0) < 2:
            raise ValueError(
                "Cannot apply pung: not enough valid tiles to pung",
            )
        self._remove_tiles(block.first_tile, 2)
        self.call_blocks.append(deepcopy(block))

    def _apply_an_kong(self, block: CallBlock) -> None:
        if self.tiles.get(block.first_tile, 0) < 4:
            raise ValueError(
                "Cannot apply ankong: not enough valid tiles to ankong",
            )
        self._remove_tiles(block.first_tile, 4)
        self.call_blocks.append(deepcopy(block))
        self.tsumo_tile = None

    def _apply_daimin_kong(self, block: CallBlock) -> None:
        if self.tiles.get(block.first_tile, 0) < 3:
            raise ValueError(
                "Cannot apply daiminkong: not enough valid tiles to daiminkong",
            )
        self._remove_tiles(block.first_tile, 3)
        self.call_blocks.append(deepcopy(block))

    def _apply_shomin_kong(self, block: CallBlock) -> None:
        if block.first_tile not in self.tiles:
            raise ValueError(
                "Cannot apply shominkong: not enough valid tiles to shominkong",
            )
        target_block: CallBlock | None = None
        for call_block in self.call_blocks:
            if (
                call_block.type == CallBlockType.PUNG
                and call_block.first_tile == block.first_tile
            ):
                target_block = call_block
                break
        if target_block is None:
            raise ValueError(
                "Cannot apply shominkong: hand doesn't have valid pung block",
            )
        self._remove_tiles(block.first_tile, 1)
        target_block.type = CallBlockType.SHOMIN_KONG
        self.tsumo_tile = None
