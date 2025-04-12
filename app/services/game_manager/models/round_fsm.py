from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
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
        print("[DEBUG] InitState: initializing round data")
        manager.init_round_data()
        print("[DEBUG] InitState: sending init events")
        await manager.send_init_events()
        print("[DEBUG] InitState: transition to FlowerState")
        return FlowerState()


class FlowerState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] FlowerState: performing init flower action")
        await manager.do_init_flower_action()
        print("[DEBUG] FlowerState: wait for init flower ok")
        await manager.wait_for_init_flower_ok()
        print(
            "[DEBUG] FlowerState: transition to TsumoState with prev_type=INIT_FLOWER",
        )
        return TsumoState(prev_type=GameEventType.INIT_FLOWER)


class TsumoState(RoundState):
    def __init__(self, prev_type: GameEventType):
        self.prev_type = prev_type
        print(f"[DEBUG] TsumoState: initialized with prev_type: {self.prev_type.name}")

    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] TsumoState: calling do_tsumo")
        next_game_event: GameEvent = await manager.do_tsumo(
            previous_event_type=self.prev_type,
        )
        print(f"[DEBUG] TsumoState: do_tsumo returned: {next_game_event}")
        state = manager.get_next_state(
            previous_event_type=GameEventType.TSUMO,
            next_event=next_game_event,
        )
        print("[DEBUG] TsumoState: transition to next state")
        return state


class ActionState(RoundState):
    def __init__(self, current_event: GameEvent):
        self.current_event = current_event
        print(f"[DEBUG] ActionState: initialized with event: {self.current_event}")

    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] ActionState: calling do_action")
        next_state: RoundState = await manager.do_action(
            current_event=self.current_event,
        )
        print("[DEBUG] ActionState: transition to next state")
        return next_state


class DiscardState(RoundState):
    def __init__(self, prev_type: GameEventType, tile: GameTile):
        self.prev_type = prev_type
        self.tile = tile
        print(
            "[DEBUG] DiscardState: initialized with prev_type:"
            " {self.prev_type.name}, tile: {self.tile}",
        )

    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] DiscardState: calling do_discard")
        next_game_event: GameEvent | None = await manager.do_discard(
            previous_turn_type=self.prev_type,
            discarded_tile=self.tile,
        )
        print(f"[DEBUG] DiscardState: do_discard returned: {next_game_event}")
        if next_game_event is None:
            print(
                "[DEBUG] DiscardState: event is None, "
                "transition to TsumoState with prev_type=DISCARD",
            )
            next_game_event = GameEvent(
                event_type=GameEventType.TSUMO,
                player_seat=AbsoluteSeat.EAST,
                action_id=-1,
                data={},
            )
        state = manager.get_next_state(
            previous_event_type=GameEventType.DISCARD,
            next_event=next_game_event,
        )
        print("[DEBUG] DiscardState: transition to next state")
        return state


class RobbingKongState(RoundState):
    def __init__(self, tile: GameTile):
        self.tile = tile
        print(f"[DEBUG] RobbingKongState: initialized with tile: {self.tile}")

    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] RobbingKongState: calling do_robbing_kong")
        next_game_event: GameEvent | None = await manager.do_robbing_kong(
            robbing_tile=self.tile,
        )
        print(f"[DEBUG] RobbingKongState: do_robbing_kong returned: {next_game_event}")
        if next_game_event is None:
            print(
                "[DEBUG] RobbingKongState: event is None, "
                "transition to TsumoState with prev_type=ROBBING_KONG",
            )
            return TsumoState(prev_type=GameEventType.ROBBING_KONG)
        state = manager.get_next_state(
            previous_event_type=GameEventType.ROBBING_KONG,
            next_event=next_game_event,
        )
        print("[DEBUG] RobbingKongState: transition to next state")
        return state


class DrawState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] DrawState: ending round as draw")
        await manager.end_round_as_draw()
        print("[DEBUG] DrawState: round ended as draw")
        return None


class HuState(RoundState):
    def __init__(self, current_event: GameEvent):
        self.current_event = current_event
        print(f"[DEBUG] HuState: initialized with event: {self.current_event}")

    async def run(self, manager: RoundManager) -> RoundState | None:
        print("[DEBUG] HuState: ending round as hu")
        await manager.end_round_as_hu(current_event=self.current_event)
        print("[DEBUG] HuState: round ended as hu")
        return None
