import pytest

from app.services.game_manager.models.enums import GameTile
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.round_fsm import (
    ActionState,
    DiscardState,
    DrawState,
    FlowerState,
    HuState,
    InitState,
    RobbingKongState,
    RoundState,
    TsumoState,
)
from app.services.game_manager.models.types import GameEventType


class DummyState(RoundState):
    async def run(self, manager) -> RoundState | None:
        return None


class FakeRoundManager:
    def __init__(self):
        self.init_called = False
        self.send_init_events_called = False
        self.do_init_flower_action_called = False
        self.do_tsumo_called = False
        self.get_next_state_called = False
        self.do_action_called = False
        self.do_discard_called = False
        self.do_robbing_kong_called = False
        self.end_round_as_draw_called = False

    def init_round_data(self):
        self.init_called = True

    async def send_init_events(self):
        self.send_init_events_called = True

    async def do_init_flower_action(self):
        self.do_init_flower_action_called = True

    async def do_tsumo(self, previous_event_type):
        self.do_tsumo_called = True
        return GameEvent(
            event_type=GameEventType.TSUMO,
            player_seat=0,
            data={},
            action_id=1,
        )

    def get_next_state(self, previous_event_type, next_event):
        self.get_next_state_called = True
        if next_event.event_type == GameEventType.TSUMO:
            return DummyState()
        return None

    async def do_action(self, current_event):
        self.do_action_called = True
        return DummyState()

    async def do_discard(self, previous_turn_type, discarded_tile):
        self.do_discard_called = True
        return GameEvent(
            event_type=GameEventType.DISCARD,
            player_seat=0,
            data={"tile": discarded_tile},
            action_id=2,
        )

    async def do_robbing_kong(self, robbing_tile):
        self.do_robbing_kong_called = True
        return GameEvent(
            event_type=GameEventType.ROBBING_KONG,
            player_seat=0,
            data={"tile": robbing_tile},
            action_id=3,
        )

    def end_round_as_draw(self):
        self.end_round_as_draw_called = True


@pytest.mark.asyncio
async def test_init_state():
    manager = FakeRoundManager()
    state = InitState()
    next_state = await state.run(manager)
    assert manager.init_called
    assert manager.send_init_events_called
    from app.services.game_manager.models.round_fsm import FlowerState

    assert isinstance(next_state, FlowerState)


@pytest.mark.asyncio
async def test_flower_state():
    manager = FakeRoundManager()
    state = FlowerState()
    next_state = await state.run(manager)
    assert manager.do_init_flower_action_called
    from app.services.game_manager.models.round_fsm import TsumoState

    assert isinstance(next_state, TsumoState)
    assert next_state.prev_type == GameEventType.DISCARD


@pytest.mark.asyncio
async def test_tsumo_state():
    manager = FakeRoundManager()
    state = TsumoState(prev_type=GameEventType.DISCARD)
    next_state = await state.run(manager)
    assert manager.do_tsumo_called
    assert manager.get_next_state_called
    assert isinstance(next_state, DummyState)


@pytest.mark.asyncio
async def test_action_state():
    manager = FakeRoundManager()
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=0,
        data={},
        action_id=1,
    )
    state = ActionState(current_event=dummy_event)
    next_state = await state.run(manager)
    assert manager.do_action_called
    assert isinstance(next_state, DummyState)


@pytest.mark.asyncio
async def test_discard_state():
    manager = FakeRoundManager()
    dummy_tile = GameTile.M1
    state = DiscardState(prev_type=GameEventType.DISCARD, tile=dummy_tile)
    next_state = await state.run(manager)
    assert manager.do_discard_called
    if next_state is not None:
        assert isinstance(next_state, DummyState)


@pytest.mark.asyncio
async def test_robbing_kong_state():
    manager = FakeRoundManager()
    dummy_tile = GameTile.M1
    state = RobbingKongState(tile=dummy_tile)
    next_state = await state.run(manager)
    assert manager.do_robbing_kong_called
    if next_state is not None:
        assert isinstance(next_state, DummyState)


@pytest.mark.asyncio
async def test_draw_state():
    manager = FakeRoundManager()
    state = DrawState()
    next_state = await state.run(manager)
    assert manager.end_round_as_draw_called
    assert next_state is None


@pytest.mark.asyncio
async def test_hu_state():
    manager = FakeRoundManager()
    state = HuState()
    next_state = await state.run(manager)
    assert next_state is None
