from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand

GENERAL_SHAPE_SIZE: Final[int] = 5
QUAD_SIZE: Final[int] = 4
TRIPLET_SIZE: Final[int] = 3
SEQUENCE_SIZE: Final[int] = 3
KNITTED_SIZE: Final[int] = 3
KNITTED_GAP: Final[int] = 3
PAIR_SIZE: Final[int] = 2
SEQUENCE_MAX_START_POINT: Final[int] = 7
FULLY_HAND_SIZE: Final[int] = 14
KNITTED_CASE: Final[list[list[Tile]]] = [
    [Tile.M1, Tile.M4, Tile.M7, Tile.S2, Tile.S5, Tile.S8, Tile.P3, Tile.P6, Tile.P9],
    [Tile.M1, Tile.M4, Tile.M7, Tile.P2, Tile.P5, Tile.P8, Tile.S3, Tile.S6, Tile.S9],
    [Tile.S1, Tile.S4, Tile.S7, Tile.M2, Tile.M5, Tile.M8, Tile.P3, Tile.P6, Tile.P9],
    [Tile.S1, Tile.S4, Tile.S7, Tile.P2, Tile.P5, Tile.P8, Tile.M3, Tile.M6, Tile.M9],
    [Tile.P1, Tile.P4, Tile.P7, Tile.M2, Tile.M5, Tile.M8, Tile.S3, Tile.S6, Tile.S9],
    [Tile.P1, Tile.P4, Tile.P7, Tile.S2, Tile.S5, Tile.S8, Tile.M3, Tile.M6, Tile.M9],
]


@dataclass
class BlockDivisionState:
    remaining_tiles_count: list[int]
    parsed_blocks: list[Block]
    current_tile: Tile
    previous_tile: Tile
    has_pair: bool
    previous_was_sequence: bool

    @staticmethod
    def create_from_hand(hand: Hand) -> BlockDivisionState:
        _remaining_tiles_count: list[int] = deepcopy(hand.tiles)
        for block in hand.call_blocks:
            if block.type == BlockType.PAIR:
                _remaining_tiles_count[block.tile] -= PAIR_SIZE
            elif block.type == BlockType.TRIPLET:
                _remaining_tiles_count[block.tile] -= TRIPLET_SIZE
            elif block.type == BlockType.QUAD:
                _remaining_tiles_count[block.tile] -= QUAD_SIZE
            elif block.type == BlockType.SEQUENCE:
                for i in range(SEQUENCE_SIZE):
                    _remaining_tiles_count[block.tile + i] -= 1
            elif block.type == BlockType.KNITTED:
                for i in range(KNITTED_SIZE):
                    _remaining_tiles_count[block.tile + i * KNITTED_GAP] -= 1
        return BlockDivisionState(
            remaining_tiles_count=_remaining_tiles_count,
            parsed_blocks=deepcopy(hand.call_blocks),
            current_tile=Tile.M1,
            previous_tile=Tile.F0,
            has_pair=False,
            previous_was_sequence=False,
        )


def divide_general_shape_knitted_sub(hand: Hand) -> list[list[Block]]:
    has_knitted_blocks: bool
    parsed_hands: list[list[Block]] = []

    for one_case in KNITTED_CASE:
        has_knitted_blocks = True
        for tile in one_case:
            if hand.tiles[tile] < 1:
                has_knitted_blocks = False
                break
        if not has_knitted_blocks:
            continue
        new_hand = deepcopy(hand)
        for i in range(0, len(one_case), KNITTED_SIZE):
            new_hand.call_blocks.append(
                Block(BlockType.KNITTED, one_case[i], is_opened=False),
            )
        parsed_hands.extend(divide_general_shape(new_hand))
    return parsed_hands


def divide_general_shape(hand: Hand) -> list[list[Block]]:
    parsed_hands: list[list[Block]] = []

    stack: list[BlockDivisionState] = []
    stack.append(BlockDivisionState.create_from_hand(hand))
    total_tiles_count: int = sum(hand.tiles)
    for block in hand.call_blocks:
        total_tiles_count -= 1 if block.type == BlockType.QUAD else 0

    if total_tiles_count != FULLY_HAND_SIZE:
        raise ValueError("Wrong hand size.")

    while stack:
        state: BlockDivisionState = stack.pop()
        next_state: BlockDivisionState

        next_tile: Tile = state.current_tile
        while next_tile < Tile.F0 and state.remaining_tiles_count[next_tile] == 0:
            next_tile = next_tile + 1
        # end point
        if next_tile >= Tile.F0:
            if len(state.parsed_blocks) == GENERAL_SHAPE_SIZE:
                parsed_hands.append(state.parsed_blocks)
            continue
        # Triplet
        if state.remaining_tiles_count[next_tile] >= TRIPLET_SIZE and (
            state.previous_tile != next_tile or not state.previous_was_sequence
        ):
            next_state = deepcopy(state)
            next_state.remaining_tiles_count[next_tile] -= TRIPLET_SIZE
            next_state.parsed_blocks.append(
                Block(type=BlockType.TRIPLET, tile=next_tile, is_opened=False),
            )
            next_state.previous_was_sequence = False
            next_state.previous_tile = next_tile
            stack.append(next_state)
        # Pair
        if (
            state.remaining_tiles_count[next_tile] >= PAIR_SIZE
            and not state.has_pair
            and (state.previous_tile != next_tile or not state.previous_was_sequence)
        ):
            next_state = deepcopy(state)
            next_state.remaining_tiles_count[next_tile] -= PAIR_SIZE
            next_state.parsed_blocks.append(
                Block(type=BlockType.PAIR, tile=next_tile, is_opened=False),
            )
            next_state.has_pair = True
            next_state.previous_was_sequence = False
            next_state.previous_tile = next_tile
            stack.append(next_state)
        # Sequence
        if (
            next_tile.is_number()
            and next_tile.get_number() <= SEQUENCE_MAX_START_POINT
            and state.remaining_tiles_count[next_tile + 1] >= 1
            and state.remaining_tiles_count[next_tile + 2] >= 1
        ):
            next_state = deepcopy(state)
            next_state.remaining_tiles_count[next_tile] -= 1
            next_state.remaining_tiles_count[next_tile + 1] -= 1
            next_state.remaining_tiles_count[next_tile + 2] -= 1
            next_state.parsed_blocks.append(
                Block(type=BlockType.SEQUENCE, tile=next_tile, is_opened=False),
            )
            next_state.previous_was_sequence = True
            next_state.previous_tile = next_tile
            stack.append(next_state)
    return parsed_hands
