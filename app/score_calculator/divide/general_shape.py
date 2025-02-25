from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand


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
        return BlockDivisionState(
            remaining_tiles_count=deepcopy(hand.tiles),
            parsed_blocks=deepcopy(hand.call_blocks),
            current_tile=Tile.M1,
            previous_tile=Tile.F0,
            has_pair=False,
            previous_was_sequence=False,
        )


GENERAL_SHAPE_SIZE: Final[int] = 5
TRIPLET_SIZE: Final[int] = 3
PAIR_SIZE: Final[int] = 2
SEQUENCE_MAX_START_POINT: Final[int] = 7
FULLY_HAND_SIZE: Final[int] = 14


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
            stack.append(next_state)
    return parsed_hands
