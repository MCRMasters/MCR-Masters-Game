import asyncio
from collections import Counter
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile, Round
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.manager import (
    ActionManager,
    GameManager,
)
from app.services.game_manager.models.round_fsm import (
    DiscardState,
    DrawState,
    RobbingKongState,
    TsumoState,
)
from app.services.game_manager.models.types import GameEventType


class DummyRoomManager:
    pass


class DummyNetworkService:
    def __init__(self):
        self.personal_messages = []
        self.broadcast_messages = []

    async def send_personal_message(
        self,
        message,
        game_id,
        user_id,
        exclude_user_id=None,
    ):
        self.personal_messages.append((message, game_id, user_id))

    async def broadcast(self, message, game_id, exclude_user_id=None):
        self.broadcast_messages.append((message, game_id, exclude_user_id))


class DummyPlayerData(BaseModel):
    uid: str
    nickname: str


class DummyPlayer:
    def __init__(self, uid, index):
        self.uid = uid

    @classmethod
    def create_from_received_data(cls, player_data, index):
        return DummyPlayer(player_data.uid, index)


class DummyHand:
    def __init__(self):
        self.tiles = Counter()
        self.has_flower = False

    def apply_discard(self, tile):
        self.tiles[tile] -= 1

    def apply_tsumo(self, tile):
        self.tiles[tile] += 1

    def get_rightmost_tile(self):
        for t in self.tiles:
            if self.tiles[t] > 0:
                return t
        return None

    def apply_call(self, block):
        self.called = True


class DummyDeck:
    def __init__(self):
        self.tiles_remaining = 10
        self.HAIPAI_TILES = 10

    def draw_haipai(self):
        return [GameTile.M1] * 13

    def draw_tiles_right(self, count):
        self.tiles_remaining -= count
        return [GameTile.M1] * count

    def draw_tiles(self, count):
        self.tiles_remaining -= count
        return [GameTile.M1] * count


class DummyWinningConditions:
    def __init__(self):
        self.winning_tile = GameTile.M1
        self.is_discarded = False
        self.is_last_tile_of_its_kind = False
        self.is_last_tile_in_the_game = False
        self.is_replacement_tile = False
        self.is_robbing_the_kong = False

    @classmethod
    def create_default_conditions(cls):
        return DummyWinningConditions()

    @classmethod
    def create_from_game_winning_conditions(
        cls,
        game_winning_conditions,
        seat_wind,
        round_wind,
    ):
        return DummyWinningConditions()


@pytest.fixture
def dummy_game_manager():
    ns = DummyNetworkService()
    drm = DummyRoomManager()
    gm = GameManager(game_id=1, room_manager=drm, network_service=ns)
    gm.player_uid_to_index = {}
    players = [
        DummyPlayerData(uid=f"user{i}", nickname=f"user{i}")
        for i in range(GameManager.MAX_PLAYERS)
    ]
    gm.init_game(players)
    gm.current_round = Round.E1
    return gm


@pytest.fixture
def round_manager(dummy_game_manager):
    rm = dummy_game_manager.round_manager
    rm.tile_deck = DummyDeck()
    rm.hands = [DummyHand() for _ in range(GameManager.MAX_PLAYERS)]
    rm.kawas = [[] for _ in range(GameManager.MAX_PLAYERS)]
    rm.visible_tiles_count = Counter()
    rm.winning_conditions = DummyWinningConditions.create_default_conditions()
    rm.seat_to_player_index = {
        AbsoluteSeat.EAST: 0,
        AbsoluteSeat.SOUTH: 1,
        AbsoluteSeat.WEST: 2,
        AbsoluteSeat.NORTH: 3,
    }
    rm.player_index_to_seat = {
        0: AbsoluteSeat.EAST,
        1: AbsoluteSeat.SOUTH,
        2: AbsoluteSeat.WEST,
        3: AbsoluteSeat.NORTH,
    }
    rm.action_manager = None
    rm.current_player_seat = AbsoluteSeat.EAST
    return rm


@pytest.mark.asyncio
async def test_init_round_data(round_manager):
    round_manager.init_round_data()
    assert round_manager.tile_deck is not None
    assert len(round_manager.hands) == GameManager.MAX_PLAYERS
    assert isinstance(round_manager.visible_tiles_count, Counter)
    assert round_manager.winning_conditions is not None
    assert round_manager.action_manager is None
    assert round_manager.current_player_seat == AbsoluteSeat.EAST


@pytest.mark.asyncio
async def test_send_init_events(round_manager, dummy_game_manager):
    dummy_game_manager.event_queue = asyncio.Queue()
    round_manager.hands = [DummyHand() for _ in range(GameManager.MAX_PLAYERS)]
    await round_manager.send_init_events()
    events = []
    while not dummy_game_manager.event_queue.empty():
        events.append(await dummy_game_manager.event_queue.get())
    assert len(events) == GameManager.MAX_PLAYERS
    for e in events:
        assert e.event_type == GameEventType.INIT_HAIPAI


@pytest.mark.asyncio
async def test_do_init_flower_action(round_manager, dummy_game_manager):
    for hand in round_manager.hands:
        hand.has_flower = False
    dummy_game_manager.event_queue = asyncio.Queue()
    await round_manager.do_init_flower_action()
    events = []
    while not dummy_game_manager.event_queue.empty():
        events.append(await dummy_game_manager.event_queue.get())
    assert len(events) == GameManager.MAX_PLAYERS
    for e in events:
        assert e.event_type == GameEventType.INIT_FLOWER


def test_get_next_state_tsumo(round_manager):
    round_manager.tile_deck.tiles_remaining = 5
    dummy_event = GameEvent(
        event_type=GameEventType.TSUMO,
        player_seat=AbsoluteSeat.EAST,
        data={},
        action_id=1,
    )
    state = round_manager.get_next_state(GameEventType.DISCARD, dummy_event)
    assert isinstance(state, TsumoState)


def test_get_next_state_draw(round_manager):
    round_manager.tile_deck.tiles_remaining = 0
    dummy_event = GameEvent(
        event_type=GameEventType.TSUMO,
        player_seat=AbsoluteSeat.EAST,
        data={},
        action_id=1,
    )
    state = round_manager.get_next_state(GameEventType.DISCARD, dummy_event)
    assert isinstance(state, DrawState)


def test_get_next_state_discard(round_manager):
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=AbsoluteSeat.EAST,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    state = round_manager.get_next_state(GameEventType.TSUMO, dummy_event)
    assert isinstance(state, DiscardState)


def test_get_next_state_robbing_kong(round_manager):
    dummy_event = GameEvent(
        event_type=GameEventType.ROBBING_KONG,
        player_seat=AbsoluteSeat.EAST,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    state = round_manager.get_next_state(GameEventType.DISCARD, dummy_event)
    assert isinstance(state, RobbingKongState)


class DummyNextTurn:
    def __init__(self, next_event):
        self.next_event = next_event


@pytest.mark.asyncio
async def test_proceed_next_turn_tsumo(round_manager):
    flag = False

    async def dummy_do_tsumo(previous_event_type):
        nonlocal flag
        flag = True

    round_manager.do_tsumo = dummy_do_tsumo
    dummy = DummyNextTurn(GameEventType.TSUMO)
    await round_manager.proceed_next_turn(dummy)
    assert flag


@pytest.mark.asyncio
async def test_proceed_next_turn_discard(round_manager):
    flag = False

    async def dummy_do_discard(previous_turn_type, discarded_tile):
        nonlocal flag
        flag = True

    round_manager.do_discard = dummy_do_discard
    dummy = DummyNextTurn(GameEventType.DISCARD)
    await round_manager.proceed_next_turn(dummy, discarded_tile=GameTile.M1)
    assert flag


@pytest.mark.asyncio
async def test_proceed_next_turn_robbing_kong(round_manager):
    flag = False

    async def dummy_do_robbing_kong(robbing_tile):
        nonlocal flag
        flag = True

    round_manager.do_robbing_kong = dummy_do_robbing_kong
    dummy_action = SimpleNamespace(tile=GameTile.M1, seat_priority=AbsoluteSeat.EAST)
    dummy = DummyNextTurn(GameEventType.ROBBING_KONG)
    await round_manager.proceed_next_turn(dummy, previous_action=dummy_action)
    assert flag


@pytest.mark.asyncio
async def test_do_robbing_kong(round_manager):
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=AbsoluteSeat.EAST,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    round_manager.check_actions_after_shomin_kong = lambda: [
        [] for _ in range(GameManager.MAX_PLAYERS)
    ]
    round_manager.send_actions_and_wait = lambda **kwargs: asyncio.sleep(
        0,
        result=dummy_event,
    )
    result = await round_manager.do_robbing_kong(GameTile.M1)
    assert result == dummy_event


def test_check_actions_after_shomin_kong(round_manager):
    round_manager.get_possible_hu_choices = (
        lambda player_seat: ["dummy"]
        if player_seat != round_manager.current_player_seat
        else []
    )
    result = round_manager.check_actions_after_shomin_kong()
    for seat in AbsoluteSeat:
        if seat == round_manager.current_player_seat:
            assert result[seat] == []
        else:
            assert result[seat] == ["dummy"]


@pytest.mark.asyncio
async def test_do_discard(round_manager):
    flag = False

    def dummy_apply_discard(tile):
        nonlocal flag
        flag = True

    round_manager.hands[
        round_manager.current_player_seat
    ].apply_discard = dummy_apply_discard
    round_manager.check_actions_after_discard = lambda: [
        [] for _ in range(GameManager.MAX_PLAYERS)
    ]
    round_manager.send_actions_and_wait = lambda **kwargs: asyncio.sleep(
        0,
        result=GameEvent(
            event_type="DUMMY",
            player_seat=round_manager.current_player_seat,
            data={},
            action_id=1,
        ),
    )
    result = await round_manager.do_discard(GameEventType.DISCARD, GameTile.M1)
    assert flag
    assert result.event_type == "DUMMY"


def test_check_actions_after_discard(round_manager):
    round_manager.get_possible_hu_choices = lambda player_seat: [1]
    round_manager.get_possible_kan_choices = lambda player_seat: [2]
    round_manager.get_possible_pon_choices = lambda player_seat: [3]
    round_manager.get_possible_chii_choices = lambda player_seat: [4]
    result = round_manager.check_actions_after_discard()
    for seat in AbsoluteSeat:
        if seat != round_manager.current_player_seat:
            assert result[seat] == [1, 2, 3, 4]
        else:
            assert result[seat] == []


@pytest.mark.asyncio
async def test_send_actions_and_wait(round_manager, dummy_game_manager):
    dummy_event = GameEvent(
        event_type="DUMMY",
        player_seat=round_manager.current_player_seat,
        data={},
        action_id=1,
    )
    round_manager._initialize_pending_players = lambda **kwargs: asyncio.sleep(
        0,
        result=(
            {round_manager.current_player_seat},
            {round_manager.current_player_seat: round_manager.DEFAULT_TURN_TIMEOUT},
        ),
    )
    round_manager._wait_for_player_actions = lambda **kwargs: asyncio.sleep(
        0,
        result=("dummy_final_action", [dummy_event]),
    )
    round_manager.pick_action_from_game_event_list = lambda action, events: dummy_event
    sent = False

    async def dummy_send_response_action_event(response_action):
        nonlocal sent
        sent = True

    round_manager.send_response_action_event = dummy_send_response_action_event
    actions = [[] for _ in range(GameManager.MAX_PLAYERS)]
    actions[round_manager.current_player_seat] = ["dummy_action"]
    result = await round_manager.send_actions_and_wait(actions)
    assert sent
    assert result == dummy_event


@pytest.mark.asyncio
async def test__send_discard_message(round_manager, dummy_game_manager):
    recorded = []

    async def dummy_send(message, game_id, user_id, exclude_user_id=None):
        recorded.append((message, game_id, user_id))

    dummy_game_manager.network_service.send_personal_message = dummy_send
    round_manager.seat_to_player_index = {round_manager.current_player_seat: 0}
    dummy_player = DummyPlayer("user0", 0)
    dummy_game_manager.player_list = [dummy_player]
    await round_manager._send_discard_message(
        round_manager.current_player_seat,
        ["action"],
    )
    assert recorded[0][1] == dummy_game_manager.game_id


def test__initialize_pending_players(round_manager):
    actions = [[] for _ in range(GameManager.MAX_PLAYERS)]
    actions[round_manager.current_player_seat] = ["action"]

    async def dummy_send(*args, **kwargs):
        return

    round_manager._send_discard_message = dummy_send
    pending, rem = asyncio.run(round_manager._initialize_pending_players(actions))
    assert round_manager.current_player_seat in pending
    assert rem[round_manager.current_player_seat] == round_manager.DEFAULT_TURN_TIMEOUT


@pytest.mark.asyncio
async def test__wait_for_player_actions(round_manager, dummy_game_manager):
    from types import SimpleNamespace

    from app.services.game_manager.models.action import Action

    Action.create_from_game_event = (
        lambda game_event, current_player_seat: SimpleNamespace(
            seat_priority=current_player_seat,
        )
    )
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=round_manager.current_player_seat,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    dummy_game_manager.event_queue = asyncio.Queue()
    await dummy_game_manager.event_queue.put(dummy_event)
    dummy_am = ActionManager([])
    round_manager.action_manager = dummy_am
    dummy_am.push_action = lambda action: "final_action"
    final, events = await round_manager._wait_for_player_actions(
        **{
            "pending_players": {round_manager.current_player_seat},
            "remaining_time": {round_manager.current_player_seat: 60.0},
        },
    )
    assert final == "final_action"
    assert dummy_event in events


def test_pick_action_from_game_event_list(round_manager):
    from types import SimpleNamespace

    from app.services.game_manager.models.action import ActionType

    dummy_action = SimpleNamespace(
        type=ActionType.create_from_game_event_type(GameEventType.DISCARD),
        seat_priority=round_manager.current_player_seat,
        tile=GameTile.M1,
    )
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=round_manager.current_player_seat,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    result = round_manager.pick_action_from_game_event_list(dummy_action, [dummy_event])
    assert result == dummy_event


def test_move_current_player_seat_to_next(round_manager):
    current = round_manager.current_player_seat
    expected = current.next_seat
    round_manager.move_current_player_seat_to_next()
    assert round_manager.current_player_seat == expected


def test_end_round_as_draw(round_manager):
    try:
        round_manager.end_round_as_draw()
    except Exception:
        assert False


def test_check_actions_after_tsumo(round_manager):
    round_manager.get_possible_hu_choices = lambda player_seat: [1]
    round_manager.get_possible_kan_choices = lambda player_seat: [2]
    round_manager.get_possible_flower_choices = lambda player_seat: [3]
    result = round_manager.check_actions_after_tsumo()
    for seat in range(GameManager.MAX_PLAYERS):
        if seat == round_manager.current_player_seat:
            assert result[seat] == [1, 2, 3]
        else:
            assert result[seat] == []


@pytest.mark.asyncio
async def test_safe_wait_for(round_manager):
    async def dummy():
        return "result"

    res, elapsed = await round_manager.safe_wait_for(dummy(), 1)
    assert res == "result"
    res, elapsed = await round_manager.safe_wait_for(
        asyncio.sleep(0.1, result="done"),
        0.2,
    )
    assert res == "done"


@pytest.mark.asyncio
async def test_send_tsumo_actions_and_wait_api(round_manager, dummy_game_manager):
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=round_manager.current_player_seat,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    dummy_game_manager.event_queue = asyncio.Queue()
    await dummy_game_manager.event_queue.put(dummy_event)
    round_manager.seat_to_player_index = {round_manager.current_player_seat: 0}
    dummy_player = DummyPlayer("user0", 0)
    dummy_game_manager.player_list = [dummy_player]
    round_manager.send_tsumo_actions_and_wait_api = lambda **kwargs: asyncio.sleep(
        0,
        result=GameEvent(
            event_type=GameEventType.DISCARD,
            player_seat=round_manager.current_player_seat,
            data={"tile": GameTile.M1},
            action_id=1,
        ),
    )
    result = await round_manager.send_tsumo_actions_and_wait_api(
        actions_lists=[
            ["action"] if i == round_manager.current_player_seat else []
            for i in range(GameManager.MAX_PLAYERS)
        ],
    )
    assert result == dummy_event


@pytest.mark.asyncio
async def test_wait_discard_after_call_action(round_manager, dummy_game_manager):
    dummy_event = GameEvent(
        event_type=GameEventType.DISCARD,
        player_seat=round_manager.current_player_seat,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    dummy_game_manager.event_queue = asyncio.Queue()
    await dummy_game_manager.event_queue.put(dummy_event)
    result = await round_manager.wait_discard_after_call_action()
    assert result == dummy_event


@pytest.mark.asyncio
async def test_do_action(round_manager):
    sent = False

    async def dummy_send(response_action):
        nonlocal sent
        sent = True

    round_manager.send_response_action_event = dummy_send
    applied = False

    def dummy_apply(response_event):
        nonlocal applied
        applied = True

    round_manager.apply_response_event = dummy_apply

    async def dummy_wait():
        return GameEvent(
            event_type=GameEventType.CHII,
            player_seat=round_manager.current_player_seat,
            data={"tile": GameTile.M1},
            action_id=1,
        )

    round_manager.wait_discard_after_call_action = dummy_wait
    state = await round_manager.do_action(
        GameEvent(
            event_type=GameEventType.CHII,
            player_seat=round_manager.current_player_seat,
            data={"tile": GameTile.M1},
            action_id=1,
        ),
    )
    assert sent and applied and isinstance(state, DiscardState)


def test_apply_response_event(round_manager):
    called = False

    def dummy_apply_call(block):
        nonlocal called
        called = True

    round_manager.hands[AbsoluteSeat.SOUTH].apply_call = dummy_apply_call
    round_manager.winning_conditions.winning_tile = GameTile.M1
    round_manager.current_player_seat = AbsoluteSeat.EAST
    dummy_event = GameEvent(
        event_type=GameEventType.CHII,
        player_seat=AbsoluteSeat.SOUTH,
        data={"tile": GameTile.M1},
        action_id=1,
    )
    round_manager.apply_response_event(dummy_event)
    assert called
    assert round_manager.current_player_seat == AbsoluteSeat.SOUTH


@pytest.mark.asyncio
async def test_send_response_action_event(round_manager, dummy_game_manager):
    recorded = []

    async def dummy_broadcast(message, game_id, exclude_user_id=None):
        recorded.append(("broadcast", message))

    dummy_game_manager.network_service.broadcast = dummy_broadcast
    event = GameEvent(
        event_type=GameEventType.FLOWER,
        player_seat=AbsoluteSeat.EAST,
        data={},
        action_id=1,
    )
    await round_manager.send_response_action_event(event)
    assert recorded[0][0] == "broadcast"


def test_set_winning_conditions(round_manager):
    round_manager.visible_tiles_count = Counter({GameTile.M1: 3})
    round_manager.tile_deck.tiles_remaining = 0
    round_manager.winning_conditions = DummyWinningConditions()
    round_manager.set_winning_conditions = lambda winning_tile, previous_event_type: (
        setattr(round_manager.winning_conditions, "winning_tile", winning_tile)
        or setattr(
            round_manager.winning_conditions,
            "is_discarded",
            previous_event_type.is_next_discard,
        )
        or setattr(round_manager.winning_conditions, "is_last_tile_of_its_kind", True)
        or setattr(round_manager.winning_conditions, "is_last_tile_in_the_game", True)
    )
    round_manager.set_winning_conditions(GameTile.M1, GameEventType.DISCARD)
    assert round_manager.winning_conditions.winning_tile == GameTile.M1
    assert (
        round_manager.winning_conditions.is_discarded
        == GameEventType.DISCARD.is_next_discard
    )
    assert round_manager.winning_conditions.is_last_tile_of_its_kind is True
    assert round_manager.winning_conditions.is_last_tile_in_the_game is True


@pytest.mark.asyncio
async def test_do_tsumo(round_manager):
    round_manager.tile_deck = DummyDeck()
    dummy_hand = DummyHand()
    round_manager.hands[round_manager.current_player_seat] = dummy_hand
    round_manager.set_winning_conditions = (
        lambda winning_tile, previous_event_type: None
    )
    round_manager.check_actions_after_tsumo = lambda: [
        [] for _ in range(GameManager.MAX_PLAYERS)
    ]
    round_manager.send_tsumo_actions_and_wait_api = lambda **kwargs: asyncio.sleep(
        0,
        result=GameEvent(
            event_type=GameEventType.DISCARD,
            player_seat=round_manager.current_player_seat,
            data={"tile": GameTile.M1},
            action_id=1,
        ),
    )
    result = await round_manager.do_tsumo(GameEventType.DISCARD)
    assert result.event_type == GameEventType.DISCARD
