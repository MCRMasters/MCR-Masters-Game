from enum import IntEnum


class Round(IntEnum):
    E1 = 0
    E2 = 1
    E3 = 2
    E4 = 3

    S1 = 4
    S2 = 5
    S3 = 6
    S4 = 7

    W1 = 8
    W2 = 9
    W3 = 10
    W4 = 11

    N1 = 12
    N2 = 13
    N3 = 14
    N4 = 15

    END = 16


class ActionType(IntEnum):
    SKIP = 0
    HU = 1
    KAN = 2
    PON = 3
    CHII = 4
    FLOWER = 5


class CallBlockType(IntEnum):
    CHII = 0
    PUNG = 1
    AN_KONG = 2
    SHOMIN_KONG = 3
    DAIMIN_KONG = 4


class Wind(IntEnum):
    EAST = 0
    SOUTH = 1
    WEST = 2
    NORTH = 3


class Seat(IntEnum):
    SELF = 0
    SHIMO = 1
    TOI = 2
    KAMI = 3


class GameTile(IntEnum):
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
    F1 = 35
    F2 = 36
    F3 = 37
    F4 = 38
    F5 = 39
    F6 = 40
    F7 = 41

    @classmethod
    def all_tiles(cls) -> range:
        return range(cls.M1, cls.F7 + 1)

    @classmethod
    def normal_tiles(cls) -> range:
        return range(cls.M1, cls.F0)

    @classmethod
    def flower_tiles(cls) -> range:
        return range(cls.F0, cls.F7 + 1)
