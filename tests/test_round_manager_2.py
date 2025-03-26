import asyncio

import pytest

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
from app.services.game_manager.models.manager import RoundManager
from app.services.game_manager.models.types import ActionType, GameEventType, TurnType

pytestmark = pytest.mark.skip(reason="Skipping all tests in this module")


class DummyGameManager:
    def __init__(self):
        self.action_id = 0
        self.current_round = 0
        self.player_list = []

    def increase_action_id(self):
        self.action_id += 1


@pytest.mark.asyncio
async def test_safe_wait_for_success():
    rm = RoundManager(game_manager=DummyGameManager())

    async def return_value():
        await asyncio.sleep(0.1)
        return "done"

    result, elapsed = await rm.safe_wait_for(return_value(), timeout=1.0)
    assert result == "done"
    assert elapsed >= 0.1


@pytest.mark.asyncio
async def test_safe_wait_for_timeout():
    rm = RoundManager(game_manager=DummyGameManager())

    async def never_finishes():
        await asyncio.sleep(2)
        return "done"

    result, elapsed = await rm.safe_wait_for(never_finishes(), timeout=0.1)
    assert result is None
    assert elapsed >= 0.1


def test_move_current_player_seat_without_previous_action():
    dummy = DummyGameManager()
    rm = RoundManager(game_manager=dummy)
    rm.current_player_seat = AbsoluteSeat.EAST
    expected_next = rm.current_player_seat.next_seat
    rm.move_current_player_seat_to_next()
    assert rm.current_player_seat == expected_next


def test_move_current_player_seat_with_previous_action(monkeypatch):
    dummy = DummyGameManager()
    rm = RoundManager(game_manager=dummy)
    rm.current_player_seat = AbsoluteSeat.EAST

    dummy_action = Action(
        type=ActionType.HU,
        seat_priority=AbsoluteSeat.EAST,
        tile=GameTile.M5,
    )

    def fake_next_seat_after_action(action):
        return AbsoluteSeat.NORTH

    monkeypatch.setattr(
        rm.current_player_seat,
        "next_seat_after_action",
        fake_next_seat_after_action,
    )
    rm.move_current_player_seat_to_next(previous_action=dummy_action)
    assert rm.current_player_seat == AbsoluteSeat.NORTH


def test_set_winning_conditions():
    dummy = DummyGameManager()
    rm = RoundManager(game_manager=dummy)
    rm.init_round()
    winning_tile = GameTile.M5
    rm.visible_tiles_count[winning_tile] = 3
    rm.tile_deck.draw_tiles(rm.tile_deck.tiles_remaining)
    rm.set_winning_conditions(winning_tile, TurnType.DISCARD)
    wc = rm.winning_conditions
    assert wc.winning_tile == winning_tile
    assert wc.is_discarded == TurnType.DISCARD.is_next_discard
    assert wc.is_last_tile_of_its_kind is True
    assert wc.is_last_tile_in_the_game is True
    assert wc.is_replacement_tile == TurnType.DISCARD.is_kong
    assert wc.is_robbing_the_kong is False


@pytest.mark.asyncio
async def test_start_round_events(monkeypatch):
    dummy = DummyGameManager()
    rm = RoundManager(game_manager=dummy)
    rm.init_round()

    async def dummy_do_flower_action(event_queue):
        pass

    monkeypatch.setattr(rm, "do_flower_action_in_init_hand", dummy_do_flower_action)
    event_queue = asyncio.Queue()
    await rm.start_round(event_queue)

    events = []
    while not event_queue.empty():
        events.append(await event_queue.get())
        event_queue.task_done()

    init_events = [e for e in events if e.event_type == GameEventType.INIT_HAIPAI]
    assert len(init_events) == 4


def test_get_possible_hu_choices():
    dummy = DummyGameManager()
    rm = RoundManager(game_manager=dummy)
    rm.init_round()
    rm.winning_conditions.winning_tile = GameTile.M5
    rm.winning_conditions.is_discarded = True
    actions = rm.get_possible_hu_choices(AbsoluteSeat.EAST)
    assert isinstance(actions, list)
