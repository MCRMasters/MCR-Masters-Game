from __future__ import annotations

from enum import IntEnum


class GameEventType(IntEnum):
    DISCARD = 0
    TSUMO = 1
    SHOMIN_KAN = 2
    DAIMIN_KAN = 3
    AN_KAN = 4
    CHII = 5
    PON = 6
    FLOWER = 7
    INIT_HAIPAI = 8
    INIT_FLOWER = 9
    HU = 10
    ROBBING_KONG = 11

    @property
    def next_event(self) -> GameEventType | None:
        match self:
            case GameEventType.TSUMO | GameEventType.CHII | GameEventType.PON:
                return GameEventType.DISCARD
            case GameEventType.SHOMIN_KAN:
                return GameEventType.ROBBING_KONG
            case GameEventType.INIT_HAIPAI:
                return GameEventType.INIT_FLOWER
            case (
                GameEventType.DISCARD
                | GameEventType.DAIMIN_KAN
                | GameEventType.AN_KAN
                | GameEventType.FLOWER
                | GameEventType.ROBBING_KONG
                | GameEventType.INIT_FLOWER
            ):
                return GameEventType.TSUMO
            case GameEventType.HU:
                return None

    @property
    def is_next_replacement(self) -> bool:
        return self in {
            GameEventType.DAIMIN_KAN,
            GameEventType.AN_KAN,
            GameEventType.FLOWER,
            GameEventType.ROBBING_KONG,
        }

    @property
    def is_next_discard(self) -> bool:
        return self in {GameEventType.TSUMO, GameEventType.PON, GameEventType.CHII}

    @property
    def is_kong(self) -> bool:
        return self in {
            GameEventType.ROBBING_KONG,
            GameEventType.DAIMIN_KAN,
            GameEventType.AN_KAN,
        }


class ActionType(IntEnum):
    SKIP = 0
    HU = 1
    KAN = 2
    PON = 3
    CHII = 4
    FLOWER = 5

    @staticmethod
    def create_from_game_event_type(
        game_event_type: GameEventType,
    ) -> ActionType | None:
        match game_event_type:
            case (
                GameEventType.SHOMIN_KAN
                | GameEventType.DAIMIN_KAN
                | GameEventType.AN_KAN
            ):
                return ActionType.KAN
            case GameEventType.CHII:
                return ActionType.CHII
            case GameEventType.PON:
                return ActionType.PON
            case GameEventType.FLOWER:
                return ActionType.FLOWER
            case GameEventType.HU:
                return ActionType.HU
            case _:
                return None


class CallBlockType(IntEnum):
    CHII = 0
    PUNG = 1
    AN_KONG = 2
    SHOMIN_KONG = 3
    DAIMIN_KONG = 4
