import asyncio

import pytest

from app.services.game_manager.models.deck import Deck
from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.round_fsm import (
    DiscardState,
    DrawState,
    FlowerState,
    HuState,
    InitState,
    RobbingKongState,
    TsumoState,
)
from app.services.game_manager.models.types import GameEventType, TurnType
from app.services.game_manager.models.winning_conditions import GameWinningConditions


class DummyRoundManager:
    def __init__(self):
        self.called_methods = []
        self.tile_deck = None
        self.hands = None
        self.kawas = None
        self.visible_tiles_count = None
        self.winning_conditions = None
        self.action_manager = None
        self.current_player_seat = AbsoluteSeat.EAST

        class DummyGameManager:
            def __init__(self):
                self.event_queue = asyncio.Queue()
                self.action_id = 0

            MAX_PLAYERS = 4

        self.game_manager = DummyGameManager()

    def init_round_data(self) -> None:
        self.called_methods.append("init_round_data")
        self.tile_deck = Deck()
        self.hands = [
            GameHand.create_from_tiles(tiles=self.tile_deck.draw_haipai())
            for _ in range(self.game_manager.MAX_PLAYERS)
        ]
        self.kawas = [[] for _ in range(self.game_manager.MAX_PLAYERS)]
        self.visible_tiles_count = {}
        self.winning_conditions = GameWinningConditions.create_default_conditions()
        self.action_manager = None
        self.current_player_seat = AbsoluteSeat.EAST

    async def send_init_events(self) -> None:
        self.called_methods.append("send_init_events")
        for seat in AbsoluteSeat:
            init_data = {"hand": self.hands[seat].tiles.elements()}
            init_event = GameEvent(
                event_type=GameEventType.INIT_HAIPAI,
                player_seat=seat,
                data=init_data,
                action_id=0,
            )
            await self.game_manager.event_queue.put(init_event)

    async def do_init_flower_action(self) -> None:
        self.called_methods.append("do_init_flower_action")

    async def do_tsumo(self, previous_turn_type: TurnType) -> None:
        self.called_methods.append(f"do_tsumo:{previous_turn_type}")

    def get_next_state(
        self,
        previous_turn_type: TurnType,
        previous_action=None,
        discarded_tile: GameTile | None = None,
    ):
        self.called_methods.append(f"get_next_state:{previous_turn_type}")

    def end_round_as_draw(self) -> None:
        self.called_methods.append("end_round_as_draw")

    def move_current_player_seat_to_next(self, previous_action=None):
        self.called_methods.append("move_current_player_seat_to_next")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "state_class, init_args, expected_call_substring",
    [
        (InitState, (), "init_round_data"),
        (FlowerState, (), "do_init_flower_action"),
        (TsumoState, (TurnType.DISCARD,), "do_tsumo"),
        (DiscardState, (TurnType.DISCARD, GameTile(0)), "get_next_state"),
        (RobbingKongState, (TurnType.DISCARD, GameTile(0)), "get_next_state"),
        (DrawState, (), "end_round_as_draw"),
        (HuState, (), None),
    ],
)
async def test_round_state(state_class, init_args, expected_call_substring):
    manager = DummyRoundManager()
    state = state_class(*init_args)
    next_state = await state.run(manager)
    if expected_call_substring is None:
        assert len(manager.called_methods) == 0
    else:
        found = any(expected_call_substring in call for call in manager.called_methods)
        assert found, (
            f"Expected '{expected_call_substring}' in called "
            "methods {manager.called_methods}"
        )
