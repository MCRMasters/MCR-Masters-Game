from collections import Counter
from unittest.mock import Mock

import pytest

from app.services.game_manager.models.deck import Deck
from app.services.game_manager.models.enums import AbsoluteSeat
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.manager import GameManager, RoundManager
from app.services.game_manager.models.types import TurnType
from app.services.game_manager.models.winning_conditions import GameWinningConditions


def test_init_round():
    gm = GameManager()
    rm = RoundManager(gm)
    rm.tile_deck = Deck()
    rm.hand_list = [
        GameHand.create_from_tiles(tiles=list(range(13)))
        for _ in range(GameManager.MAX_PLAYERS)
    ]
    rm.kawa_list = [[] for _ in range(GameManager.MAX_PLAYERS)]
    rm.visible_tiles_count = Counter()
    rm.winning_conditions = GameWinningConditions.create_default_conditions()
    rm.current_player_seat = AbsoluteSeat.EAST
    rm.init_round()
    assert isinstance(rm.hand_list, list)
    assert len(rm.hand_list) == GameManager.MAX_PLAYERS
    assert isinstance(rm.kawa_list, list)
    assert isinstance(rm.visible_tiles_count, Counter)
    assert hasattr(rm.winning_conditions, "winning_tile")
    assert rm.current_player_seat is not None


@pytest.mark.parametrize(
    "previous_action, expected_seat",
    [
        (None, AbsoluteSeat((AbsoluteSeat.EAST + 1) % 4)),
        (Mock(seat_priority=2), AbsoluteSeat((AbsoluteSeat.EAST + 2) % 4)),
    ],
)
def test_move_current_player_seat_to_next(previous_action, expected_seat):
    gm = GameManager()
    rm = RoundManager(gm)
    rm.current_player_seat = AbsoluteSeat.EAST
    rm.move_current_player_seat_to_next(previous_action)
    assert rm.current_player_seat == expected_seat


@pytest.mark.parametrize(
    "previous_turn, previous_action, expected_method",
    [
        (TurnType.DISCARD, None, "do_discard"),
        (TurnType.TSUMO, Mock(seat_priority=1), "do_tsumo"),
    ],
)
def test_proceed_next_turn(
    monkeypatch,
    previous_turn,
    previous_action,
    expected_method,
):
    gm = GameManager()
    rm = RoundManager(gm)
    rm.current_player_seat = AbsoluteSeat.EAST
    called = {}

    def fake_do_tsumo(previous_turn_type, **kwargs):
        called["method"] = "do_tsumo"
        previous_turn_type, kwargs

    def fake_do_discard(previous_turn_type, **kwargs):
        called["method"] = "do_discard"
        previous_turn_type, kwargs

    monkeypatch.setattr(rm, "do_tsumo", fake_do_tsumo)
    monkeypatch.setattr(rm, "do_discard", fake_do_discard)
    mock_turn = Mock()
    mock_turn.next_turn = previous_turn
    mock_turn.is_next_replacement = False
    mock_turn.is_next_discard = previous_turn == TurnType.DISCARD
    mock_turn.is_kong = False
    rm.proceed_next_turn(mock_turn, previous_action)
    assert "method" in called
    assert called["method"] == expected_method
