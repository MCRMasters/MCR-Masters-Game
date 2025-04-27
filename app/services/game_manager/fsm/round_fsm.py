from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.types import GameEventType

if TYPE_CHECKING:
    from app.services.game_manager.manager import RoundManager

logger = logging.getLogger(__name__)


class RoundState(ABC):
    @abstractmethod
    async def run(self, manager: RoundManager) -> RoundState | None:
        pass


class InitState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("InitState: initializing round data")
        manager.init_round_data()
        logger.debug("InitState: sending init events")
        await manager.send_init_events()
        logger.debug("InitState: transition to FlowerState")
        return FlowerState()


class FlowerState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("FlowerState: performing init flower action")
        await manager.do_init_flower_action()
        logger.debug("FlowerState: wait for init flower ok")
        await manager.wait_for_init_flower_ok()
        logger.debug(
            "FlowerState: transition to TsumoState with prev_type=INIT_FLOWER",
        )
        return TsumoState(prev_type=GameEventType.INIT_FLOWER)


class TsumoState(RoundState):
    def __init__(self, prev_type: GameEventType):
        self.prev_type = prev_type
        logger.debug(
            "TsumoState: initialized with prev_type: %s",
            self.prev_type.name,
        )

    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("TsumoState: calling do_tsumo")
        next_game_event: GameEvent = await manager.do_tsumo(
            previous_event_type=self.prev_type,
        )
        logger.debug("TsumoState: do_tsumo returned: %s", next_game_event)
        state = manager.get_next_state(
            previous_event_type=GameEventType.TSUMO,
            next_event=next_game_event,
        )
        logger.debug("TsumoState: transition to next state")
        return state


class ActionState(RoundState):
    def __init__(self, current_event: GameEvent):
        self.current_event = current_event
        logger.debug("ActionState: initialized with event: %s", self.current_event)

    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("ActionState: calling do_action")
        next_state: RoundState = await manager.do_action(
            current_event=self.current_event,
        )
        logger.debug("ActionState: transition to next state")
        return next_state


class DiscardState(RoundState):
    def __init__(self, prev_type: GameEventType, tile: GameTile):
        self.prev_type = prev_type
        self.tile = tile
        logger.debug(
            "DiscardState: initialized with prev_type: %s, tile: %s",
            self.prev_type.name,
            self.tile,
        )

    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("DiscardState: calling do_discard")
        next_game_event: GameEvent | None = await manager.do_discard(
            previous_turn_type=self.prev_type,
            discarded_tile=self.tile,
        )
        logger.debug("DiscardState: do_discard returned: %s", next_game_event)

        if next_game_event is None:
            logger.debug(
                "DiscardState: event is None, transition "
                "to TsumoState with prev_type=DISCARD",
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
        logger.debug("DiscardState: transition to next state")
        return state


class RobbingKongState(RoundState):
    def __init__(self, tile: GameTile):
        self.tile = tile
        logger.debug("RobbingKongState: initialized with tile: %s", self.tile)

    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("RobbingKongState: calling do_robbing_kong")
        next_game_event: GameEvent | None = await manager.do_robbing_kong(
            robbing_tile=self.tile,
        )
        logger.debug(
            "RobbingKongState: do_robbing_kong returned: %s",
            next_game_event,
        )

        if next_game_event is None:
            logger.debug(
                "RobbingKongState: event is None, transition to "
                "TsumoState with prev_type=ROBBING_KONG",
            )
            return TsumoState(prev_type=GameEventType.ROBBING_KONG)

        state = manager.get_next_state(
            previous_event_type=GameEventType.ROBBING_KONG,
            next_event=next_game_event,
        )
        logger.debug("RobbingKongState: transition to next state")
        return state


class DrawState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("DrawState: ending round as draw")
        await manager.end_round_as_draw()
        logger.debug("DrawState: round ended as draw")
        return WaitingNextRoundState()


class HuState(RoundState):
    def __init__(self, current_event: GameEvent):
        self.current_event = current_event
        logger.debug("HuState: initialized with event: %s", self.current_event)

    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug("HuState: ending round as hu")
        await manager.end_round_as_hu(current_event=self.current_event)
        logger.debug("HuState: round ended as hu")
        return WaitingNextRoundState()


class WaitingNextRoundState(RoundState):
    async def run(self, manager: RoundManager) -> RoundState | None:
        logger.debug(
            "WaitingNextRoundState: Waiting for NEXT_ROUND_CONFIRM responses",
        )
        await manager.wait_for_next_round_confirm()
        logger.debug(
            "WaitingNextRoundState: All confirmations received or timeout occurred",
        )
        return None
