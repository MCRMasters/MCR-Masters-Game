from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class GameWebSocketActionType(str, Enum):
    PING = "ping"
    PONG = "pong"
    USER_JOINED = "user_joined"
    ERROR = "error"
    DRAW = "draw"
    DISCARD = "discard"


class MessageEventType(str, Enum):
    INIT_FLOWER_REPLACEMENT = "init_flower_replacement"
    GAME_START_INFO = "game_start_info"
    INIT_EVENT = "init_event"
    HAIPAI_HAND = "haipai_hand"
    TSUMO_ACTIONS = "tsumo_actions"
    DISCARD_ACTIONS = "discard_actions"
    DISCARD = "discard"
    TSUMO = "tsumo"
    CHII = "chii"
    PON = "pon"
    DAIMIN_KAN = "daimin_kan"
    SHOMIN_KAN = "shomin_kan"
    AN_KAN = "an_kan"
    FLOWER = "flower"
    OPEN_AN_KAN = "open_an_kan"
    HU_HAND = "hu_hand"
    PING = "ping"
    PONG = "pong"
    USER_JOINED = "user_joined"
    ERROR = "error"


class WebSocketResponse(BaseModel):
    status: Literal["success", "error"]
    action: GameWebSocketActionType
    data: dict[str, Any] | None = {}
    error: str | None = None


class WebSocketMessage(BaseModel):
    action: GameWebSocketActionType
    data: dict[str, Any] | None = None


class WSMessage(BaseModel):
    event: MessageEventType
    data: dict[str, Any]
