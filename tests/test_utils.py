from typing import Final

from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand


def tile_to_name(tile: Tile) -> str:
    return tile.name.lower()[::-1]


def name_to_tile(name: str) -> Tile:
    d: Final[dict[str, int]] = {"m": 0, "p": 1, "s": 2, "z": 3}
    return Tile(int(name[0]) - 1 + d[name[1]] * 9) if name[1] != "f" else Tile.F0


# [] Open Pung/Kong, {} Closed Kong
def raw_string_to_hand_class(string: str) -> Hand:
    tile_stack: list[str] = []
    block_type: BlockType
    tiles_count: list[int] = [0] * 34
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
                    tile=name_to_tile("".join(tile_stack[-2:])),
                    is_opened=c == "]",
                ),
            )
            tile_stack.clear()
        elif c.isdigit():
            tile_stack.append(c)
        elif c in {"m", "p", "s", "z"}:
            if call_mode:
                tile_stack.append(c)
                continue
            for num in tile_stack:
                print("tile:", num + c, name_to_tile(num + c))
                tiles_count[name_to_tile(num + c)] += 1

            tile_stack.clear()
    return Hand(tiles_count, blocks_list)
