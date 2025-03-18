from collections import Counter
from unittest.mock import Mock

import pytest

from app.services.game_manager.models.call_block import CallBlock
from app.services.game_manager.models.enums import AbsoluteSeat, GameTile, RelativeSeat
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.manager import GameManager, RoundManager
from app.services.game_manager.models.types import CallBlockType, TurnType
from app.services.game_manager.models.winning_conditions import GameWinningConditions
from app.services.score_calculator.block.block import Block
from app.services.score_calculator.enums.enums import BlockType, Tile, Wind
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)


@pytest.mark.parametrize(
    "winning_tile, hand_tiles, expected_chii_count, description",
    [
        (
            GameTile.M5,
            {GameTile.M3: 1, GameTile.M4: 1, GameTile.M5: 1},
            0,
            "Last tile in game returns no chii",
        ),
        (GameTile.Z1, {GameTile.Z1: 3}, 0, "Honor tile returns no chii"),
        (
            GameTile.M5,
            {GameTile.M3: 1, GameTile.M4: 1, GameTile.M5: 1},
            1,
            "Valid chii with M3, M4, M5",
        ),
        (GameTile.M5, {GameTile.M4: 1, GameTile.M5: 1}, 0, "Missing M3 for chii"),
    ],
)
def test_get_possible_chii_actions(
    winning_tile,
    hand_tiles,
    expected_chii_count,
    description,
):
    wc = GameWinningConditions.create_default_conditions()
    wc.winning_tile = winning_tile
    if "Last tile" in description:
        wc.is_last_tile_in_the_game = True
    else:
        wc.is_last_tile_in_the_game = False
    wc.is_discarded = True
    hand = GameHand(tiles=hand_tiles.copy(), call_blocks=[])
    rs = RelativeSeat.SHIMO
    actions = hand.get_possible_chii_actions(priority=rs, winning_condition=wc)
    assert len(actions) == expected_chii_count, description


@pytest.mark.parametrize(
    "winning_tile, hand_tiles, is_discarded, expected_pon_count, description",
    [
        (
            GameTile.M5,
            {GameTile.M5: 2},
            True,
            1,
            "Valid pon action when tile count>=2 and discarded",
        ),
        (GameTile.M5, {GameTile.M5: 1}, True, 0, "Not enough tiles for pon"),
        (GameTile.M5, {GameTile.M5: 3}, False, 0, "Not discarded -> no pon action"),
    ],
)
def test_get_possible_pon_actions(
    winning_tile,
    hand_tiles,
    is_discarded,
    expected_pon_count,
    description,
):
    wc = GameWinningConditions.create_default_conditions()
    wc.winning_tile = winning_tile
    wc.is_last_tile_in_the_game = False
    wc.is_discarded = is_discarded
    hand = GameHand(tiles=hand_tiles.copy(), call_blocks=[])
    rs = RelativeSeat.KAMI
    actions = hand.get_possible_pon_actions(priority=rs, winning_condition=wc)
    assert len(actions) == expected_pon_count, description


@pytest.mark.parametrize(
    "winning_tile, hand_tiles, is_discarded, expected_kan_count, description",
    [
        (GameTile.M5, {GameTile.M5: 3}, True, 1, "Discarded: valid kan when count>=3"),
        (GameTile.M5, {GameTile.M5: 2}, True, 0, "Discarded: not enough for kan"),
        (GameTile.M4, {GameTile.M5: 4}, False, 1, "Non-discarded: ankan when count==4"),
        (
            GameTile.M5,
            {GameTile.M5: 3},
            False,
            1,
            "Non-discarded: ankan when count==3 and matching tile",
        ),
    ],
)
def test_get_possible_kan_actions(
    winning_tile,
    hand_tiles,
    is_discarded,
    expected_kan_count,
    description,
):
    wc = GameWinningConditions.create_default_conditions()
    wc.winning_tile = winning_tile
    wc.is_last_tile_in_the_game = False
    wc.is_discarded = is_discarded
    hand = GameHand(tiles=hand_tiles.copy(), call_blocks=[])
    rs = RelativeSeat.TOI
    actions = hand.get_possible_kan_actions(priority=rs, winning_condition=wc)
    assert len(actions) == expected_kan_count, description


@pytest.mark.parametrize(
    "winning_tile, hand_tiles, call_tile, call_type, expected_kan_count, description",
    [
        (
            GameTile.M5,
            {GameTile.M3: 1, GameTile.M5: 1},
            GameTile.M5,
            CallBlockType.PUNG,
            1,
            "Call block matching winning_tile triggers kan",
        ),
        (
            GameTile.M5,
            {GameTile.M3: 1},
            GameTile.M5,
            CallBlockType.PUNG,
            1,
            "Call block triggered even if tile missing in hand",
        ),
    ],
)
def test_get_possible_kan_actions_with_call_block(
    winning_tile,
    hand_tiles,
    call_tile,
    call_type,
    expected_kan_count,
    description,
):
    wc = GameWinningConditions.create_default_conditions()
    wc.winning_tile = winning_tile
    wc.is_last_tile_in_the_game = False
    wc.is_discarded = False
    cb = CallBlock(
        first_tile=call_tile,
        type=call_type,
        source_tile_index=0,
        source_seat=AbsoluteSeat.EAST,
    )
    hand = GameHand(tiles=hand_tiles.copy(), call_blocks=[cb])
    rs = RelativeSeat.TOI
    actions = hand.get_possible_kan_actions(priority=rs, winning_condition=wc)
    assert len(actions) == expected_kan_count, description


@pytest.mark.parametrize(
    "current_seat, target_seat, expected",
    [
        (0, 0, 0),
        (0, 1, 1),
        (3, 0, 1),
        (2, 0, 2),
    ],
)
def test_create_relative_seat(current_seat, target_seat, expected):
    rs = RelativeSeat.create_from_absolute_seats(current_seat, target_seat)
    assert rs == expected


@pytest.mark.parametrize(
    "turn, expected_next",
    [
        (TurnType.TSUMO, TurnType.DISCARD),
        (TurnType.CHII, TurnType.DISCARD),
        (TurnType.PON, TurnType.DISCARD),
        (TurnType.SHOMIN_KAN, TurnType.ROBBING_KONG),
        (TurnType.DAIMIN_KAN, TurnType.TSUMO),
    ],
)
def test_turn_type_next_turn(turn, expected_next):
    assert turn.next_turn == expected_next


@pytest.mark.parametrize(
    "call_type, expected_block_type",
    [
        (CallBlockType.CHII, BlockType.SEQUENCE),
        (CallBlockType.PUNG, BlockType.TRIPLET),
        (CallBlockType.AN_KONG, BlockType.QUAD),
    ],
)
def test_create_block_from_call_block(call_type, expected_block_type):
    cb = CallBlock(
        first_tile=GameTile.M3,
        type=call_type,
        source_tile_index=0,
        source_seat=AbsoluteSeat.EAST,
    )
    block = Block.create_from_call_block(cb)
    assert block.tile == Tile(cb.first_tile)
    assert block.is_opened == (call_type == CallBlockType.AN_KONG)
    assert block.type == expected_block_type


def test_create_hand_from_game_hand():
    original_tiles = {GameTile.M1: 2, GameTile.M2: 3}
    original_call_blocks = []
    gh = GameHand(tiles=original_tiles.copy(), call_blocks=original_call_blocks)
    new_hand = Hand.create_from_game_hand(gh)
    assert new_hand.tiles[GameTile.M1] == 2
    assert new_hand.tiles[GameTile.M2] == 3


def test_create_winning_conditions_from_game():
    gwc = GameWinningConditions.create_default_conditions()
    gwc.winning_tile = GameTile.M5
    seat_wind = AbsoluteSeat.EAST
    round_wind = AbsoluteSeat.SOUTH
    wc = WinningConditions.create_from_game_winning_conditions(
        game_winning_conditions=gwc,
        seat_wind=seat_wind,
        round_wind=round_wind,
    )
    print(wc)
    print(gwc)
    print(wc is gwc)
    assert wc.winning_tile == gwc.winning_tile
    assert wc.seat_wind == Wind.create_from_absolute_seat(seat_wind)
    assert wc.round_wind == Wind.create_from_absolute_seat(round_wind)


def test_round_manager_init_round():
    gm = GameManager()
    rm = RoundManager(gm)
    rm.init_round()
    assert isinstance(rm.hands, list)
    assert len(rm.hands) == GameManager.MAX_PLAYERS
    assert isinstance(rm.kawas, list)
    assert isinstance(rm.visible_tiles_count, Counter)
    assert hasattr(rm.winning_conditions, "winning_tile")
    assert rm.current_player_seat is not None


@pytest.mark.parametrize(
    "prev_turn, discarded_tile, expected_method",
    [
        (TurnType.DISCARD, GameTile.M1, "do_discard"),
        (TurnType.TSUMO, None, "do_tsumo"),
    ],
)
def test_round_manager_proceed_next_turn(
    monkeypatch,
    prev_turn,
    discarded_tile,
    expected_method,
):
    gm = GameManager()
    rm = RoundManager(gm)
    rm.init_round()
    called = []

    def fake_do_discard(*args, **kwargs):
        called.append("do_discard")

    def fake_do_tsumo(*args, **kwargs):
        called.append("do_tsumo")

    monkeypatch.setattr(rm, "do_discard", fake_do_discard)
    monkeypatch.setattr(rm, "do_tsumo", fake_do_tsumo)
    mock_turn = Mock()
    mock_turn.next_turn = prev_turn
    mock_turn.is_next_replacement = False
    mock_turn.is_next_discard = prev_turn == TurnType.DISCARD
    mock_turn.is_kong = False
    rm.proceed_next_turn(mock_turn, discarded_tile=discarded_tile)
    assert called[0] == expected_method


@pytest.mark.parametrize(
    "is_replacement, expected_draw_method",
    [
        (True, "draw_tiles_right"),
        (False, "draw_tiles"),
    ],
)
def test_do_tsumo(monkeypatch, is_replacement, expected_draw_method):
    gm = GameManager()
    rm = RoundManager(gm)
    rm.init_round()
    monkeypatch.setattr(rm, "check_actions_after_tsumo", lambda: [])

    class FakeTurn:
        is_next_replacement = is_replacement

    fake_turn = FakeTurn()
    expected_tile = GameTile.M1

    def fake_draw_tiles(count):
        return [expected_tile] * count

    def fake_draw_tiles_right(count):
        return [expected_tile] * count

    if is_replacement:
        monkeypatch.setattr(rm.tile_deck, "draw_tiles_right", fake_draw_tiles_right)
    else:
        monkeypatch.setattr(rm.tile_deck, "draw_tiles", fake_draw_tiles)
    applied_tiles = []

    def fake_apply_tsumo(self, tile):
        applied_tiles.append(tile)

    monkeypatch.setattr(GameHand, "apply_tsumo", fake_apply_tsumo)
    wc_called = {}

    def fake_set_winning_conditions(winning_tile, previous_turn_type):
        wc_called["winning_tile"] = winning_tile
        wc_called["previous_turn_type"] = previous_turn_type

    monkeypatch.setattr(rm, "set_winning_conditions", fake_set_winning_conditions)
    tsumo_actions_called = False

    def fake_send_tsumo_actions_and_wait_api(actions_lists):
        nonlocal tsumo_actions_called
        tsumo_actions_called = True

    monkeypatch.setattr(
        rm,
        "send_tsumo_actions_and_wait_api",
        fake_send_tsumo_actions_and_wait_api,
    )
    rm.do_tsumo(previous_turn_type=fake_turn)
    assert applied_tiles[0] == expected_tile, (
        "do_tsumo: apply_tsumo should be called with the drawn tile"
    )
    assert wc_called.get("winning_tile") == expected_tile, (
        "do_tsumo: winning_tile should be set to drawn tile"
    )
    assert tsumo_actions_called, (
        "do_tsumo: send_tsumo_actions_and_wait_api should be called"
    )


@pytest.mark.parametrize(
    "discarded_tile, initial_visible, expected_visible",
    [
        (GameTile.M1, 0, 1),
        (GameTile.M2, 2, 3),
    ],
)
def test_do_discard(monkeypatch, discarded_tile, initial_visible, expected_visible):
    gm = GameManager()
    rm = RoundManager(gm)
    rm.init_round()
    rm.current_player_seat = AbsoluteSeat.EAST
    rm.visible_tiles_count[discarded_tile] = initial_visible
    monkeypatch.setattr(rm, "check_actions_after_discard", lambda: [])
    discard_called = []

    def fake_apply_discard(self, tile):
        discard_called.append(tile)

    monkeypatch.setattr(GameHand, "apply_discard", fake_apply_discard)
    wc_called = {}

    def fake_set_winning_conditions(winning_tile, previous_turn_type):
        wc_called["winning_tile"] = winning_tile

    monkeypatch.setattr(rm, "set_winning_conditions", fake_set_winning_conditions)
    discard_api_called = False

    def fake_send_actions_and_wait_api(actions_lists):
        nonlocal discard_api_called
        discard_api_called = True

    monkeypatch.setattr(rm, "send_actions_and_wait_api", fake_send_actions_and_wait_api)
    rm.do_discard(
        previous_turn_type=Mock(is_next_discard=True),
        discarded_tile=discarded_tile,
    )
    assert discard_called[0] == discarded_tile, (
        "do_discard: apply_discard should be called with discarded_tile"
    )
    assert rm.visible_tiles_count.get(discarded_tile) == expected_visible, (
        "do_discard: visible_tiles_count should increase"
    )
    assert wc_called.get("winning_tile") == discarded_tile, (
        "do_discard: winning_tile should be set to discarded_tile"
    )
    assert discard_api_called, "do_discard: send_actions_and_wait_api should be called"


@pytest.mark.parametrize(
    "robbing_tile",
    [GameTile.M2, GameTile.M3],
)
def test_do_robbing_kong(monkeypatch, robbing_tile):
    gm = GameManager()
    rm = RoundManager(gm)
    rm.init_round()
    wc_called = {}

    def fake_set_winning_conditions(winning_tile, previous_turn_type):
        wc_called["winning_tile"] = winning_tile

    monkeypatch.setattr(rm, "set_winning_conditions", fake_set_winning_conditions)
    expected_actions = [[Mock() for _ in range(GameManager.MAX_PLAYERS)]]
    monkeypatch.setattr(rm, "check_actions_after_shomin_kong", lambda: expected_actions)
    actions_sent = []

    def fake_send_actions_and_wait_api(actions_lists):
        actions_sent.append(actions_lists)

    monkeypatch.setattr(rm, "send_actions_and_wait_api", fake_send_actions_and_wait_api)
    fake_turn = Mock()
    rm.do_robbing_kong(previous_turn_type=fake_turn, robbing_tile=robbing_tile)
    assert wc_called.get("winning_tile") == robbing_tile, (
        "do_robbing_kong: winning_tile should be set to robbing_tile"
    )
    assert actions_sent[0] == expected_actions, (
        "do_robbing_kong: send_actions_and_wait_api"
        "should be called with expected actions"
    )
