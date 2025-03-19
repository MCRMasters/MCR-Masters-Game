from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class GameWebSocketActionType(str, Enum):
    PING = "ping"
    PONG = "pong"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ERROR = "error"
    DRAW = "draw"
    DISCARD = "discard"


class WebSocketResponse(BaseModel):
    status: Literal["success", "error"]
    action: GameWebSocketActionType
    data: dict[str, Any] | None = {}
    error: str | None = None


class WebSocketMessage(BaseModel):
    action: GameWebSocketActionType
    data: dict[str, Any] | None = None
