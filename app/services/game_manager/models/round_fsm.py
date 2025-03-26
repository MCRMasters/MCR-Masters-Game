from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.services.game_manager.models.enums import GameTile
from app.services.game_manager.models.types import TurnType

if TYPE_CHECKING:
    from app.services.game_manager.models.manager import RoundManager


class RoundState(ABC):
    @abstractmethod
    async def run(self, manager: RoundManager) -> RoundState | None:
        pass


class InitState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        manager.init_round_data()
        await manager.send_init_events()
        return FlowerState()


class FlowerState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        await manager.do_init_flower_action()
        return TsumoState(previous_turn_type=TurnType.DISCARD)


class TsumoState(RoundState):
    def __init__(self, previous_turn_type: TurnType):
        self.prev_type = previous_turn_type

    async def run(self, manager: RoundManager) -> RoundState | None:
        await manager.do_tsumo(previous_turn_type=self.prev_type)
        return manager.get_next_state(previous_turn_type=TurnType.TSUMO)


# TODO
class DiscardState(RoundState):
    def __init__(self, prev_type: TurnType, tile: GameTile):
        self.prev_type = prev_type
        self.tile = tile

    async def run(self, manager: RoundManager) -> RoundState | None:
        # TODO
        return manager.get_next_state(
            previous_turn_type=TurnType.DISCARD,
            discarded_tile=self.tile,
        )


# TODO
class RobbingKongState(RoundState):
    def __init__(self, prev_type: TurnType, tile: GameTile):
        self.prev_type = prev_type
        self.tile = tile

    async def run(self, manager: RoundManager) -> RoundState | None:
        # TODO
        return manager.get_next_state(previous_turn_type=TurnType.ROBBING_KONG)


# TODO
class DrawState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        # TODO
        manager.end_round_as_draw()
        return None


# TODO
class HuState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        # TODO
        manager
        return None
