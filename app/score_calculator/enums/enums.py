from __future__ import annotations

from enum import Enum, IntEnum


class BlockType(Enum):
    SEQUENCE = 0
    TRIPLET = 1
    QUAD = 2
    PAIR = 3
    KNITTED = 4


class Wind(IntEnum):
    EAST = 27
    SOUTH = 28
    WEST = 29
    NORTH = 30


class Tile(IntEnum):
    """Tile enumeration for Mahjong.

    This enum categorizes Mahjong tiles into five groups:
    - M (Manzu tile)
    - P (Pinzu tile)
    - S (Souzu tile)
    - Z (Honor tile)
    - F (Flower tile)

    Attributes:
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

    @property
    def is_honor(self) -> bool:
        return Tile.Z1 <= self.value <= Tile.Z7

    @property
    def is_number(self) -> bool:
        return Tile.M1 <= self.value <= Tile.S9

    @property
    def is_manzu(self) -> bool:
        return Tile.M1 <= self.value <= Tile.M9

    @property
    def is_pinzu(self) -> bool:
        return Tile.P1 <= self.value <= Tile.P9

    @property
    def is_souzu(self) -> bool:
        return Tile.S1 <= self.value <= Tile.S9

    @property
    def is_wind(self) -> bool:
        return Tile.Z1 <= self.value <= Tile.Z4

    @property
    def is_dragon(self) -> bool:
        return Tile.Z5 <= self.value <= Tile.Z7

    @property
    def is_terminal(self) -> bool:
        return self.value in {Tile.M1, Tile.M9, Tile.P1, Tile.P9, Tile.S1, Tile.S9}

    @property
    def is_outside(self) -> bool:
        return self.is_terminal or self.is_honor

    @property
    def number(self) -> int:
        return self.value % 9 + 1 if self.is_number else 0

    @property
    def type(self) -> str:
        return self.name[0]

    @classmethod
    def all_tiles(cls) -> range:
        return range(cls.M1, cls.F0)

    @classmethod
    def number_tiles(cls) -> range:
        return range(cls.M1, cls.Z1)

    @classmethod
    def honor_tiles(cls) -> range:
        return range(cls.Z1, cls.F0)

    @classmethod
    def outside_tiles(cls) -> tuple[Tile, ...]:
        return (
            cls.M1,
            cls.M9,
            cls.P1,
            cls.P9,
            cls.S1,
            cls.S9,
            cls.Z1,
            cls.Z2,
            cls.Z3,
            cls.Z4,
            cls.Z5,
            cls.Z6,
            cls.Z7,
        )

    def __add__(self, value: int) -> Tile:
        return Tile(self.value + value)


class Yaku(Enum):
    ERROR = -1
    ChickenHand = 0
    SevenShiftedPairs = 1
    ThirteenOrphans = 2
    BigFourWinds = 3
    BigThreeDragons = 4
    NineGates = 5
    AllGreen = 6
    FourKongs = 7
    FourConcealedPungs = 8
    AllTerminals = 9
    LittleFourWinds = 10
    LittleThreeDragons = 11
    AllHonors = 12
    PureTerminalChows = 13
    QuadrupleChow = 14
    FourPureShiftedPungs = 15
    FourPureShiftedChows = 16
    ThreeKongs = 17
    AllTerminalsAndHonors = 18
    SevenPairs = 19
    GreaterHonorsAndKnittedTiles = 20
    AllEvenPungs = 21
    FullFlush = 22
    UpperTiles = 23
    MiddleTiles = 24
    LowerTiles = 25
    PureTripleChow = 26
    PureShiftedPungs = 27
    PureStraight = 28
    ThreeSuitedTerminalChows = 29
    PureShiftedChows = 30
    AllFives = 31
    TriplePung = 32
    ThreeConcealedPungs = 33
    LesserHonorsAndKnittedTiles = 34
    KnittedStraight = 35
    UpperFour = 36
    LowerFour = 37
    BigThreeWinds = 38
    LastTileDraw = 39
    LastTileClaim = 40
    OutWithReplacementTile = 41
    RobbingTheKong = 42
    MixedStraight = 43
    MixedTripleChow = 44
    ReversibleTiles = 45
    MixedShiftedPungs = 46
    TwoConcealedKongs = 47
    MeldedHand = 48
    MixedShiftedChows = 49
    AllPungs = 50
    HalfFlush = 51
    AllTypes = 52
    TwoDragonsPungs = 53
    FullyConcealedHand = 54
    LastTile = 55
    OutsideHand = 56
    TwoMeldedKongs = 57
    ConcealedHand = 58
    DragonPung = 59
    PrevalentWind = 60
    SeatWind = 61
    AllChows = 62
    DoublePung = 63
    TwoConcealedPungs = 64
    TileHog = 65
    ConcealedKong = 66
    AllSimples = 67
    PureDoubleChow = 68
    MixedDoubleChow = 69
    ShortStraight = 70
    TwoTerminalChows = 71
    PungOfTerminalsOrHonors = 72
    OneVoidedSuit = 73
    NoHonorTiles = 74
    MeldedKong = 75
    EdgeWait = 76
    SingleWait = 77
    ClosedWait = 78
    SelfDrawn = 79
