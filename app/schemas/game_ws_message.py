from typing import Any, Literal

from pydantic import BaseModel

# 밑은 예시이고 변경가능
ActionType = Literal[
    "authenticateRequest",
    "authenticateResponse",
]


class BaseGameWebSocketMessage(BaseModel):
    action: ActionType
    data: dict[str, Any]

    class Config:
        extra = "forbid"


class AuthenticateRequestData(BaseModel):
    access_token: str
    client_uid: str


class AuthenticateResponseData(BaseModel):
    success: bool
    message: str
    client_uid: str | None


class AuthenticateRequest(BaseGameWebSocketMessage):
    action: Literal["authenticateRequest"]
    data: AuthenticateRequestData


class AuthenticateResponse(BaseGameWebSocketMessage):
    action: Literal["authenticateResponse"]
    data: AuthenticateResponseData


GameWebSocketMessage = AuthenticateRequest | AuthenticateResponse
