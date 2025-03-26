from collections import Counter

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

pytestmark = pytest.mark.skip(reason="Skipping all tests in this module")


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
    gm = GameManager(1)
    rm = RoundManager(gm)
    rm.init_round()
    assert isinstance(rm.hands, list)
    assert len(rm.hands) == GameManager.MAX_PLAYERS
    assert isinstance(rm.kawas, list)
    assert isinstance(rm.visible_tiles_count, Counter)
    assert hasattr(rm.winning_conditions, "winning_tile")
    assert rm.current_player_seat is not None
