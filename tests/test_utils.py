from typing import Final

from app.services.score_calculator.block.block import Block
from app.services.score_calculator.enums.enums import BlockType, Tile, Wind
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)


def tile_to_name(tile: Tile) -> str:
    return tile.name.lower()[::-1]


def name_to_tile(name: str) -> Tile:
    d: Final[dict[str, int]] = {"m": 0, "p": 1, "s": 2, "z": 3}
    return Tile(int(name[0]) - 1 + d[name[1]] * 9) if name[1] != "f" else Tile.F0


# [] Open Pung/Kong, {} Closed Kong
def raw_string_to_hand_class(string: str) -> Hand:
    tile_stack: list[str] = []
    block_type: BlockType
    tiles_count: list[int] = [0] * 35
    blocks_list: list[Block] = []
    four: int = 4
    call_mode: bool = False

    for c in string:
        if c in {"[", "{"}:
            call_mode = True
            tile_stack.clear()
        elif c in {"]", "}"}:
            call_mode = False
            if len(tile_stack) == four:
                block_type = (
                    BlockType.SEQUENCE
                    if len(set(tile_stack)) == four
                    else BlockType.TRIPLET
                )
            elif len(tile_stack) == four + 1:
                block_type = BlockType.QUAD
            else:
                continue
            blocks_list.append(
                Block(
                    type=block_type,
                    tile=name_to_tile("".join(tile_stack[0] + tile_stack[-1])),
                    is_opened=c == "]",
                ),
            )
            tile_stack.clear()
        elif c.isdigit():
            tile_stack.append(c)
        elif c in {"m", "p", "s", "z"}:
            for num in tile_stack:
                # print("tile:", num + c, name_to_tile(num + c))
                tiles_count[name_to_tile(num + c)] += 1
            if call_mode:
                tile_stack.append(c)
            else:
                tile_stack.clear()
    return Hand(tiles_count, blocks_list)


SEQUENCE_SIZE: Final[int] = 3


def print_blocks(blocks: list[Block]):
    for block in blocks:
        print_block(block)
    print()


BLOCKTYPE_SIZE: dict[BlockType, int] = {
    BlockType.PAIR: 2,
    BlockType.TRIPLET: 3,
    BlockType.QUAD: 4,
}


def print_block(block: Block):
    if block.is_opened:
        print("[", end="")
    elif block.type == BlockType.QUAD:
        print("{", end="")
    if block.type in {BlockType.PAIR, BlockType.TRIPLET, BlockType.QUAD}:
        print(tile_to_name(block.tile) * BLOCKTYPE_SIZE[block.type], end="")
    elif block.type == BlockType.SEQUENCE:
        for i in range(SEQUENCE_SIZE):
            print(tile_to_name(block.tile + i), end="")
    elif block.type == BlockType.KNITTED:
        for i in range(SEQUENCE_SIZE):
            print(tile_to_name(block.tile + i * SEQUENCE_SIZE), end="")
    if block.is_opened:
        print("]", end="")
    elif block.type == BlockType.QUAD:
        print("}", end="")
    print(" ", end="")


def create_default_winning_conditions(
    winning_tile: Tile,
    is_discarded: bool = True,
    count_tenpai_tiles: int = 1,
    seat_wind: Wind = Wind.EAST,
    round_wind: Wind = Wind.EAST,
    **extra_conditions,
):
    defaults = {
        "is_last_tile_in_the_game": False,
        "is_last_tile_of_its_kind": False,
        "is_replacement_tile": False,
        "is_robbing_the_kong": False,
    }
    defaults.update(extra_conditions)
    return WinningConditions(
        winning_tile=winning_tile,
        is_discarded=is_discarded,
        count_tenpai_tiles=count_tenpai_tiles,
        seat_wind=seat_wind,
        round_wind=round_wind,
        is_last_tile_in_the_game=defaults["is_last_tile_in_the_game"],
        is_last_tile_of_its_kind=defaults["is_last_tile_of_its_kind"],
        is_replacement_tile=defaults["is_replacement_tile"],
        is_robbing_the_kong=defaults["is_robbing_the_kong"],
    )
