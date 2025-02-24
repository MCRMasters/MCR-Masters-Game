from app.score_calculator.enums.enums import Tile


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
