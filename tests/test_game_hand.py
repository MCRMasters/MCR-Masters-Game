from collections import Counter
from copy import deepcopy

import pytest

from app.services.game_manager.models.call_block import CallBlock
from app.services.game_manager.models.enums import GameTile
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.types import CallBlockType


@pytest.mark.parametrize(
    "params",
    [
        (
            Counter({GameTile.M1: 4, GameTile.M2: 4, GameTile.M3: 4, GameTile.M4: 1}),
            [],
            None,
            GameTile.M6,
            Counter(
                {
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 4,
                    GameTile.M4: 1,
                    GameTile.M6: 1,
                },
            ),
            GameTile.M6,
        ),
        (
            Counter({GameTile.M3: 3, GameTile.M4: 3, GameTile.M5: 3, GameTile.M6: 4}),
            [],
            None,
            GameTile.M3,
            Counter({GameTile.M3: 4, GameTile.M4: 3, GameTile.M5: 3, GameTile.M6: 4}),
            GameTile.M3,
        ),
    ],
)
def test_apply_tsumo(params):
    (
        initial_tiles,
        call_blocks,
        tsumo_tile,
        tile_to_add,
        expected_tiles,
        expected_tsumo,
    ) = params
    hand = GameHand(
        tiles=deepcopy(initial_tiles),
        call_blocks=deepcopy(call_blocks),
        tsumo_tile=tsumo_tile,
    )
    hand.apply_tsumo(tile_to_add)
    assert hand.tiles == expected_tiles
    assert hand.tsumo_tile == expected_tsumo


def test_apply_tsumo_full_hand():
    hand = GameHand(tiles=Counter({GameTile.M2: 14}), call_blocks=[])
    with pytest.raises(ValueError, match="Cannot apply tsumo: hand is already full."):
        hand.apply_tsumo(GameTile.M3)


@pytest.mark.parametrize(
    "params",
    [
        (
            Counter(
                {
                    GameTile.M4: 2,
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 4,
                },
            ),
            GameTile.M4,
            GameTile.M4,
            Counter(
                {
                    GameTile.M4: 1,
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 4,
                },
            ),
        ),
        (
            Counter(
                {
                    GameTile.M8: 1,
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 4,
                    GameTile.M4: 1,
                },
            ),
            GameTile.M8,
            GameTile.M8,
            Counter(
                {
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 4,
                    GameTile.M4: 1,
                },
            ),
        ),
    ],
)
def test_apply_discard(params):
    initial_tiles, tsumo_tile, tile_to_discard, expected_tiles = params
    hand = GameHand(tiles=deepcopy(initial_tiles), call_blocks=[])
    hand.tsumo_tile = tsumo_tile
    hand.apply_discard(tile_to_discard)
    assert hand.tiles == expected_tiles
    assert hand.tsumo_tile is None


def test_apply_discard_tile_not_in_hand():
    hand = GameHand(
        tiles=Counter(
            {
                GameTile.M5: 1,
                GameTile.M1: 4,
                GameTile.M2: 4,
                GameTile.M3: 4,
            },
        ),
        call_blocks=[],
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply discard: hand doesn't have tile ",
    ):
        hand.apply_discard(GameTile.M6)


@pytest.mark.parametrize(
    "params",
    [
        (
            Counter(
                {
                    GameTile.M3: 1,
                    GameTile.M4: 1,
                    GameTile.M5: 1,
                    GameTile.M7: 4,
                    GameTile.M8: 4,
                    GameTile.M9: 2,
                },
            ),
            CallBlock(
                source_tile_index=0,
                source_seat=0,
                type=CallBlockType.CHII,
                first_tile=GameTile.M3,
            ),
            Counter(
                {
                    GameTile.M3: 1,
                    GameTile.M7: 4,
                    GameTile.M8: 4,
                    GameTile.M9: 2,
                },
            ),
        ),
    ],
)
def test_apply_call_chii(params):
    initial_tiles, block, expected_tiles = params
    hand = GameHand(tiles=deepcopy(initial_tiles), call_blocks=[])
    hand.apply_call(block)
    assert hand.tiles == expected_tiles
    assert len(hand.call_blocks) == 1


def test_apply_call_chii_failure():
    init = Counter(
        {
            GameTile.M3: 1,
            GameTile.M4: 1,
            GameTile.M7: 4,
            GameTile.M8: 4,
            GameTile.M9: 3,
        },
    )
    hand = GameHand(tiles=init, call_blocks=[])
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.CHII,
        first_tile=GameTile.M3,
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply chii: not enough valid tiles to chii",
    ):
        hand.apply_call(block)


@pytest.mark.parametrize(
    "params",
    [
        (
            Counter(
                {
                    GameTile.M6: 2,
                    GameTile.M7: 1,
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 2,
                },
            ),
            CallBlock(
                source_tile_index=0,
                source_seat=0,
                type=CallBlockType.PUNG,
                first_tile=GameTile.M6,
            ),
            Counter(
                {
                    GameTile.M7: 1,
                    GameTile.M1: 4,
                    GameTile.M2: 4,
                    GameTile.M3: 2,
                },
            ),
        ),
    ],
)
def test_apply_call_pung(params):
    initial_tiles, block, expected_tiles = params
    hand = GameHand(tiles=deepcopy(initial_tiles), call_blocks=[])
    hand.apply_call(block)
    assert hand.tiles == expected_tiles
    assert len(hand.call_blocks) == 1


def test_apply_call_pung_failure():
    init = Counter(
        {
            GameTile.M8: 1,
            GameTile.M1: 4,
            GameTile.M2: 4,
            GameTile.M3: 4,
        },
    )
    hand = GameHand(tiles=init, call_blocks=[])
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.PUNG,
        first_tile=GameTile.M8,
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply pung: not enough valid tiles to pung",
    ):
        hand.apply_call(block)


@pytest.mark.parametrize(
    "params",
    [
        (
            Counter(
                {
                    GameTile.P1: 4,
                    GameTile.M2: 2,
                    GameTile.M3: 4,
                    GameTile.M4: 4,
                },
            ),
            CallBlock(
                source_tile_index=0,
                source_seat=0,
                type=CallBlockType.AN_KONG,
                first_tile=GameTile.P1,
            ),
            Counter(
                {
                    GameTile.M2: 2,
                    GameTile.M3: 4,
                    GameTile.M4: 4,
                },
            ),
        ),
    ],
)
def test_apply_call_an_kong(params):
    initial_tiles, block, expected_tiles = params
    hand = GameHand(tiles=deepcopy(initial_tiles), call_blocks=[])
    hand.apply_call(block)
    assert hand.tiles == expected_tiles
    assert len(hand.call_blocks) == 1
    assert hand.tsumo_tile is None


def test_apply_call_an_kong_failure():
    init = Counter(
        {
            GameTile.M4: 3,
            GameTile.M1: 4,
            GameTile.M2: 4,
            GameTile.M3: 3,
        },
    )
    hand = GameHand(tiles=init, call_blocks=[])
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.AN_KONG,
        first_tile=GameTile.M4,
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply ankong: not enough valid tiles to ankong",
    ):
        hand.apply_call(block)


@pytest.mark.parametrize(
    "params",
    [
        (
            Counter(
                {
                    GameTile.M5: 3,
                    GameTile.M1: 4,
                    GameTile.M2: 3,
                    GameTile.M3: 3,
                },
            ),
            CallBlock(
                source_tile_index=0,
                source_seat=0,
                type=CallBlockType.DAIMIN_KONG,
                first_tile=GameTile.M5,
            ),
            Counter(
                {
                    GameTile.M1: 4,
                    GameTile.M2: 3,
                    GameTile.M3: 3,
                },
            ),
        ),
    ],
)
def test_apply_call_daimin_kong(params):
    initial_tiles, block, expected_tiles = params
    hand = GameHand(tiles=deepcopy(initial_tiles), call_blocks=[])
    hand.apply_call(block)
    assert hand.tiles == expected_tiles
    assert len(hand.call_blocks) == 1


def test_apply_call_daimin_kong_failure():
    init = Counter(
        {
            GameTile.M7: 2,
            GameTile.M1: 4,
            GameTile.M2: 4,
            GameTile.M3: 3,
        },
    )
    hand = GameHand(tiles=init, call_blocks=[])
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.DAIMIN_KONG,
        first_tile=GameTile.M7,
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply daiminkong: not enough valid tiles to daiminkong",
    ):
        hand.apply_call(block)


def test_apply_call_shomin_kong_success():
    init = Counter(
        {
            GameTile.M9: 1,
            GameTile.M6: 2,
            GameTile.M1: 4,
            GameTile.M2: 4,
        },
    )
    pung_block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.PUNG,
        first_tile=GameTile.M9,
    )
    call_blocks = [pung_block]
    hand = GameHand(tiles=deepcopy(init), call_blocks=deepcopy(call_blocks))
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.SHOMIN_KONG,
        first_tile=GameTile.M9,
    )
    hand.apply_call(block)
    expected = Counter(
        {
            GameTile.M6: 2,
            GameTile.M1: 4,
            GameTile.M2: 4,
        },
    )
    assert hand.tiles == expected
    assert hand.call_blocks[0].type == CallBlockType.SHOMIN_KONG
    assert hand.tsumo_tile is None


def test_apply_call_shomin_kong_failure_no_tile():
    init = Counter(
        {
            GameTile.M1: 4,
            GameTile.M2: 4,
            GameTile.M4: 3,
        },
    )
    pung_block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.PUNG,
        first_tile=GameTile.M3,
    )
    hand = GameHand(tiles=deepcopy(init), call_blocks=[pung_block])
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.SHOMIN_KONG,
        first_tile=GameTile.M3,
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply shominkong: not enough valid tiles to shominkong",
    ):
        hand.apply_call(block)


def test_apply_call_shomin_kong_failure_no_pung():
    init = Counter(
        {
            GameTile.M4: 1,
            GameTile.M1: 4,
            GameTile.M2: 3,
            GameTile.M3: 3,
        },
    )
    hand = GameHand(tiles=deepcopy(init), call_blocks=[])
    block = CallBlock(
        source_tile_index=0,
        source_seat=0,
        type=CallBlockType.SHOMIN_KONG,
        first_tile=GameTile.M4,
    )
    with pytest.raises(
        ValueError,
        match="Cannot apply shominkong: hand doesn't have valid pung block",
    ):
        hand.apply_call(block)
