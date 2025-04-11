import pytest

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.round_fsm import (
    ActionState,
    DiscardState,
    FlowerState,
    HuState,
    InitState,
    RobbingKongState,
    TsumoState,
)
from app.services.game_manager.models.types import GameEventType

pytestmark = pytest.mark.skip(reason="모든 테스트 스킵")


class DummyRoundManager:
    def __init__(self):
        self.init_called = False
        self.send_init_events_called = False
        self.do_init_flower_called = False
        self.do_tsumo_called = False
        self.do_action_called = False
        self.do_discard_called = False
        self.do_robbing_kong_called = False
        self.end_round_as_hu_called = False

    def init_round_data(self) -> None:
        self.init_called = True

    async def send_init_events(self) -> None:
        self.send_init_events_called = True

    async def do_init_flower_action(self) -> None:
        self.do_init_flower_called = True

    async def do_tsumo(self, previous_event_type: GameEventType) -> GameEvent:
        self.do_tsumo_called = True
        return GameEvent(
            event_type=GameEventType.TSUMO,
            player_seat=AbsoluteSeat.EAST,
            data={"tile": GameTile.M1},
            action_id=1,
        )

    async def do_action(self, current_event: GameEvent) -> object:
        self.do_action_called = True
        return DiscardState(prev_type=GameEventType.DISCARD, tile=GameTile.M1)

    async def do_discard(
        self,
        previous_turn_type: GameEventType,
        discarded_tile: GameTile,
    ) -> GameEvent | None:
        self.do_discard_called = True
        return None

    async def do_robbing_kong(self, robbing_tile: GameTile) -> GameEvent | None:
        self.do_robbing_kong_called = True
        return None

    def get_next_state(
        self,
        previous_event_type: GameEventType,
        next_event: GameEvent,
    ) -> object:
        return TsumoState(prev_type=next_event.event_type)

    def increase_action_id(self) -> None:
        pass

    @property
    def default_turn_timeout(self) -> float:
        return 60.0

    async def end_round_as_hu(self, current_event: GameEvent) -> None:
        self.end_round_as_hu_called = True


@pytest.mark.asyncio
async def test_init_state():
    manager = DummyRoundManager()
    state = InitState()
    next_state = await state.run(manager)
    assert manager.init_called
    assert manager.send_init_events_called
    from app.services.game_manager.models.round_fsm import FlowerState

    assert isinstance(next_state, FlowerState)


@pytest.mark.asyncio
async def test_flower_state():
    manager = DummyRoundManager()
    state = FlowerState()
    next_state = await state.run(manager)
    assert manager.do_init_flower_called
    from app.services.game_manager.models.round_fsm import TsumoState

    assert isinstance(next_state, TsumoState)
    assert next_state.prev_type == GameEventType.DISCARD


@pytest.mark.asyncio
async def test_tsumo_state():
    manager = DummyRoundManager()
    state = TsumoState(prev_type=GameEventType.DISCARD)
    next_state = await state.run(manager)
    assert manager.do_tsumo_called
    assert isinstance(next_state, TsumoState)


@pytest.mark.asyncio
async def test_action_state():
    manager = DummyRoundManager()
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=AbsoluteSeat.EAST,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    state = ActionState(current_event=dummy_event)
    next_state = await state.run(manager)
    assert manager.do_action_called
    assert isinstance(next_state, DiscardState)


@pytest.mark.asyncio
async def test_discard_state_returns_tsumo_state_when_none():
    manager = DummyRoundManager()
    state = DiscardState(prev_type=GameEventType.DISCARD, tile=GameTile.M1)
    next_state = await state.run(manager)
    from app.services.game_manager.models.round_fsm import TsumoState

    assert isinstance(next_state, TsumoState)
    assert next_state.prev_type == GameEventType.DISCARD


@pytest.mark.asyncio
async def test_discard_state_returns_next_state():
    class DummyManager(DummyRoundManager):
        async def do_discard(
            self,
            previous_turn_type: GameEventType,
            discarded_tile: GameTile,
        ) -> GameEvent | None:
            self.do_discard_called = True
            return GameEvent(
                event_type=GameEventType.DISCARD,
                player_seat=AbsoluteSeat.EAST,
                data={"tile": discarded_tile},
                action_id=2,
            )

    manager = DummyManager()
    state = DiscardState(prev_type=GameEventType.DISCARD, tile=GameTile.M1)
    next_state = await state.run(manager)
    assert manager.do_discard_called
    from app.services.game_manager.models.round_fsm import TsumoState

    assert isinstance(next_state, TsumoState)


@pytest.mark.asyncio
async def test_robbing_kong_state_returns_tsumo_state_when_none():
    manager = DummyRoundManager()
    state = RobbingKongState(tile=GameTile.M1)
    next_state = await state.run(manager)
    from app.services.game_manager.models.round_fsm import TsumoState

    assert isinstance(next_state, TsumoState)
    assert next_state.prev_type == GameEventType.ROBBING_KONG


@pytest.mark.asyncio
async def test_robbing_kong_state_returns_next_state():
    class DummyManager(DummyRoundManager):
        async def do_robbing_kong(self, robbing_tile: GameTile) -> GameEvent | None:
            self.do_robbing_kong_called = True
            return GameEvent(
                event_type=GameEventType.ROBBING_KONG,
                player_seat=AbsoluteSeat.EAST,
                data={"tile": robbing_tile},
                action_id=3,
            )

    manager = DummyManager()
    state = RobbingKongState(tile=GameTile.M1)
    next_state = await state.run(manager)
    assert manager.do_robbing_kong_called
    from app.services.game_manager.models.round_fsm import TsumoState

    # Dummy get_next_state returns TsumoState
    assert isinstance(next_state, TsumoState)


@pytest.mark.asyncio
async def test_hu_state():
    manager = DummyRoundManager()
    dummy_event = GameEvent(
        event_type=GameEventType.HU,
        player_seat=AbsoluteSeat.EAST,
        data={"tile": GameTile.M1},
        action_id=4,
    )
    state = HuState(current_event=dummy_event)
    next_state = await state.run(manager)
    assert manager.end_round_as_hu_called
    assert next_state is None
