from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.services.game_manager.models.enums import GameTile
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.types import GameEventType

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
        return TsumoState(prev_type=GameEventType.DISCARD)


class TsumoState(RoundState):
    def __init__(self, prev_type: GameEventType):
        self.prev_type = prev_type

    async def run(self, manager: RoundManager) -> RoundState | None:
        next_game_event: GameEvent = await manager.do_tsumo(
            previous_event_type=self.prev_type,
        )
        return manager.get_next_state(
            previous_event_type=GameEventType.TSUMO,
            next_event=next_game_event,
        )


class ActionState(RoundState):
    def __init__(self, current_event: GameEvent):
        self.current_event = current_event

    async def run(self, manager: RoundManager) -> RoundState | None:
        next_state: RoundState = await manager.do_action(
            current_event=self.current_event,
        )
        return next_state


# TODO
class DiscardState(RoundState):
    def __init__(self, prev_type: GameEventType, tile: GameTile):
        self.prev_type = prev_type
        self.tile = tile

    async def run(self, manager: RoundManager) -> RoundState | None:
        next_game_event: GameEvent | None = await manager.do_discard(
            previous_turn_type=self.prev_type,
            discarded_tile=self.tile,
        )
        if next_game_event is None:
            return TsumoState(prev_type=GameEventType.DISCARD)
        return manager.get_next_state(
            previous_event_type=GameEventType.DISCARD,
            next_event=next_game_event,
        )


class RobbingKongState(RoundState):
    def __init__(self, tile: GameTile):
        self.tile = tile

    async def run(self, manager: RoundManager) -> RoundState | None:
        next_game_event: GameEvent | None = await manager.do_robbing_kong(
            robbing_tile=self.tile,
        )
        if next_game_event is None:
            return TsumoState(prev_type=GameEventType.ROBBING_KONG)
        return manager.get_next_state(
            previous_event_type=GameEventType.ROBBING_KONG,
            next_event=next_game_event,
        )


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
