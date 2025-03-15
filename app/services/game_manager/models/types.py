from __future__ import annotations

from enum import IntEnum


class TurnType(IntEnum):
    TSUMO = 0
    DISCARD = 1
    SHOMIN_KAN = 2
    DAIMIN_KAN = 3
    AN_KAN = 4
    CHII = 5
    PON = 6
    FLOWER = 7

    @property
    def next_turn(self) -> TurnType:
        return (
            TurnType.DISCARD
            if self in {TurnType.TSUMO, TurnType.CHII, TurnType.PON}
            else TurnType.TSUMO
        )

    @property
    def is_next_replacement(self) -> bool:
        return self in {
            TurnType.SHOMIN_KAN,
            TurnType.DAIMIN_KAN,
            TurnType.AN_KAN,
            TurnType.FLOWER,
        }

    @property
    def is_next_discard(self) -> bool:
        return self in {TurnType.TSUMO, TurnType.PON, TurnType.CHII}

    @property
    def is_kong(self) -> bool:
        return self in {TurnType.SHOMIN_KAN, TurnType.DAIMIN_KAN, TurnType.AN_KAN}


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
