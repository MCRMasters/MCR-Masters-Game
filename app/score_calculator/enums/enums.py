from enum import Enum


class BlockType(Enum):
    ERROR = -1
    SEQUENCE = 0
    TRIPLET = 1
    QUAD = 2
    PAIR = 3
    KNITTED = 4


class Wind(Enum):
    EAST = 27
    SOUTH = 28
    WEST = 29
    NORTH = 30


class Tile(Enum):
    """Tile enumeration for Mahjong.

    This enum categorizes Mahjong tiles into five groups:
    - M (Manzu tile)
    - P (Pinzu tile)
    - S (Souzu tile)
    - Z (Honor tile)
    - F (Flower tile)

    Attributes:
        ERROR (int): Error

        M1 (int): Manzu 1
        M2 (int): Manzu 2
        M3 (int): Manzu 3
        M4 (int): Manzu 4
        M5 (int): Manzu 5
        M6 (int): Manzu 6
        M7 (int): Manzu 7
        M8 (int): Manzu 8
        M9 (int): Manzu 9

        P1 (int): Pinzu 1
        P2 (int): Pinzu 2
        P3 (int): Pinzu 3
        P4 (int): Pinzu 4
        P5 (int): Pinzu 5
        P6 (int): Pinzu 6
        P7 (int): Pinzu 7
        P8 (int): Pinzu 8
        P9 (int): Pinzu 9

        S1 (int): Souzu 1
        S2 (int): Souzu 2
        S3 (int): Souzu 3
        S4 (int): Souzu 4
        S5 (int): Souzu 5
        S6 (int): Souzu 6
        S7 (int): Souzu 7
        S8 (int): Souzu 8
        S9 (int): Souzu 9

        Z1 (int): Honor tile 1 (East)
        Z2 (int): Honor tile 2 (South)
        Z3 (int): Honor tile 3 (West)
        Z4 (int): Honor tile 4 (North)
        Z5 (int): Honor tile 5 (White Dragon)
        Z6 (int): Honor tile 6 (Green Dragon)
        Z7 (int): Honor tile 7 (Red Dragon)

        F0 (int): Flower tile
    """

    # Error
    ERROR = -1

    # Manzu tiles (M)
    M1 = 0
    M2 = 1
    M3 = 2
    M4 = 3
    M5 = 4
    M6 = 5
    M7 = 6
    M8 = 7
    M9 = 8

    # Pinzu tiles (P)
    P1 = 9
    P2 = 10
    P3 = 11
    P4 = 12
    P5 = 13
    P6 = 14
    P7 = 15
    P8 = 16
    P9 = 17

    # Souzu tiles (S)
    S1 = 18
    S2 = 19
    S3 = 20
    S4 = 21
    S5 = 22
    S6 = 23
    S7 = 24
    S8 = 25
    S9 = 26

    # Honor tiles (Z)
    Z1 = 27
    Z2 = 28
    Z3 = 29
    Z4 = 30
    Z5 = 31
    Z6 = 32
    Z7 = 33

    # Flower tile (F)
    F0 = 34
