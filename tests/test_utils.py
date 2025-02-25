from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import BlockType, Tile
from app.score_calculator.hand.hand import Hand


def tile_to_name(tile: Tile) -> str:
    return tile.name.lower()[::-1]


name_to_tile: dict[str, Tile] = {
    "1m": Tile.M1,
    "2m": Tile.M2,
    "3m": Tile.M3,
    "4m": Tile.M4,
    "5m": Tile.M5,
    "6m": Tile.M6,
    "7m": Tile.M7,
    "8m": Tile.M8,
    "9m": Tile.M9,
    "1p": Tile.P1,
    "2p": Tile.P2,
    "3p": Tile.P3,
    "4p": Tile.P4,
    "5p": Tile.P5,
    "6p": Tile.P6,
    "7p": Tile.P7,
    "8p": Tile.P8,
    "9p": Tile.P9,
    "1s": Tile.S1,
    "2s": Tile.S2,
    "3s": Tile.S3,
    "4s": Tile.S4,
    "5s": Tile.S5,
    "6s": Tile.S6,
    "7s": Tile.S7,
    "8s": Tile.S8,
    "9s": Tile.S9,
    "1z": Tile.Z1,
    "2z": Tile.Z2,
    "3z": Tile.Z3,
    "4z": Tile.Z4,
    "5z": Tile.Z5,
    "6z": Tile.Z6,
    "7z": Tile.Z7,
    "0f": Tile.F0,
}


# [] Open Pung/Kong, {} Closed Kong
def raw_string_to_hand_class(string: str) -> Hand:
    tile_stack: list[str] = []
    block_type: BlockType
    tiles_count: list[int] = [0] * 34
    blocks_list: list[Block] = []
    four: int = 4

    for c in string:
        if c in {"[", "{"}:
            tile_stack.clear()
        elif c in {"]", "}"}:
            if len(tile_stack) == four:
                if len(set(tile_stack)) == four:
                    block_type = BlockType.SEQUENCE
                else:
                    block_type = BlockType.TRIPLET
            elif len(tile_stack) == four + 1:
                block_type = BlockType.QUAD
            else:
                continue
            blocks_list.append(
                Block(
                    type=block_type,
                    tile=name_to_tile[tile_stack[-2:]],
                    is_opened=c == "]",
                ),
            )
            tile_stack.clear()
        elif c.isdigit():
            tile_stack.append(c)
        elif c in {"m", "p", "s", "z"}:
            for num in tile_stack:
                tiles_count[name_to_tile[num + c]] += 1

            tile_stack.clear()
    return Hand.create_from_tiles(tiles=tiles_count, call_blocks=blocks_list)
