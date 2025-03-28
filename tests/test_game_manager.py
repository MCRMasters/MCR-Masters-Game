import asyncio
from collections import Counter

import pytest

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile, Round
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.manager import GameManager


class DummyRoomManager:
    pass


class DummyNetworkService:
    async def send_personal_message(
        self,
        message,
        game_id,
        user_id,
        exclude_user_id=None,
    ):
        pass

    async def broadcast(self, message, game_id, exclude_user_id=None):
        pass


class DummyPlayerData:
    def __init__(self, uid):
        self.uid = uid


class DummyPlayer:
    def __init__(self, uid, index):
        self.uid = uid

    @classmethod
    def create_from_received_data(cls, player_data, index):
        return DummyPlayer(player_data.uid, index)


@pytest.fixture
def game_manager(monkeypatch):
    monkeypatch.setattr(
        "app.services.game_manager.models.player.Player.create_from_received_data",
        DummyPlayer.create_from_received_data,
    )
    gm = GameManager(
        game_id=1,
        room_manager=DummyRoomManager(),
        network_service=DummyNetworkService(),
    )
    gm.player_uid_to_index = {}
    player_datas = [DummyPlayerData(f"user{i}") for i in range(GameManager.MAX_PLAYERS)]
    gm.init_game(player_datas)
    gm.round_manager.player_index_to_seat = dict(
        enumerate(
            [
                AbsoluteSeat.EAST,
                AbsoluteSeat.SOUTH,
                AbsoluteSeat.WEST,
                AbsoluteSeat.NORTH,
            ],
        ),
    )
    return gm


@pytest.mark.asyncio
async def test_init_game(game_manager):
    gm = game_manager
    assert len(gm.player_list) == GameManager.MAX_PLAYERS
    expected_uids = {f"user{i}" for i in range(GameManager.MAX_PLAYERS)}
    actual_uids = {player.uid for player in gm.player_list}
    assert actual_uids == expected_uids
    assert gm.round_manager is not None
    assert isinstance(gm.event_queue, asyncio.Queue)
    assert gm.action_id == 0
    assert isinstance(gm.current_round, Round)


def test_increase_action_id(game_manager):
    gm = game_manager
    current = gm.action_id
    gm.increase_action_id()
    assert gm.action_id == current + 1


def test_get_valid_discard_result(game_manager):
    gm = game_manager
    index = gm.player_uid_to_index["user0"]
    seat = gm.round_manager.player_index_to_seat[index]

    class DummyHand:
        def __init__(self):
            self.tiles = Counter()

    dummy_hand = DummyHand()
    dummy_hand.tiles[GameTile.M1] = 1
    gm.round_manager.hands = {seat: dummy_hand}
    result = gm.get_valid_discard_result("user0", GameTile.M1)
    assert "seat" in result
    result_empty = gm.get_valid_discard_result("user0", GameTile.M9)
    assert result_empty == {}


@pytest.mark.asyncio
async def test_enqueue_event(game_manager):
    gm = game_manager
    event = GameEvent(event_type="TEST", player_seat=0, data={}, action_id=0)
    await gm.enqueue_event(event)
    queued_event = await gm.event_queue.get()
    assert queued_event == event


@pytest.mark.asyncio
async def test_start_game(game_manager):
    gm = game_manager
    call_count = 0

    async def dummy_run_round():
        nonlocal call_count
        call_count += 1

    gm.round_manager.run_round = dummy_run_round

    async def dummy_submit_game_result():
        return None

    gm.submit_game_result = dummy_submit_game_result
    await gm.start_game()
    assert call_count == GameManager.TOTAL_ROUNDS


@pytest.mark.asyncio
async def test_submit_game_result(game_manager):
    gm = game_manager
    result = await gm.submit_game_result()
    assert result is None
