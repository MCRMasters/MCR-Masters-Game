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
    GAME_EVENT = "game_event"
    RETURN_ACTION = "return_action"
    RELOAD_DATA = "reload_data"
    EMOJI_SEND = "emoji_send"
    EMOJI_BROADCAST = "emoji_broadcast"
    REQUEST_RELOAD = "request_reload"

    INIT_FLOWER_REPLACEMENT = "init_flower_replacement"
    GAME_START_INFO = "game_start_info"
    INIT_EVENT = "init_event"
    HAIPAI_HAND = "haipai_hand"
    TSUMO_ACTIONS = "tsumo_actions"
    DISCARD_ACTIONS = "discard_actions"
    ROBBING_KONG_ACTIONS = "robbing_kong_actions"
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
    SUCCESS = "success"
    ERROR = "error"
    UPDATE_ACTION_ID = "update_action_id"
    SET_TIMER = "set_timer"
    DRAW = "draw"
    END_GAME = "end_game"


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
