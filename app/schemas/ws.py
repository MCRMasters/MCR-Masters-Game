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
    GAME_STARTED = "game_started"
    WEBSOCKET_URL = "websocket_url"


class WebSocketResponse(BaseModel):
    status: Literal["success", "error"]
    action: GameWebSocketActionType
    data: dict[str, Any] | None = {}
    error: str | None = None


class WebSocketMessage(BaseModel):
    action: GameWebSocketActionType
    data: dict[str, Any] | None = None
