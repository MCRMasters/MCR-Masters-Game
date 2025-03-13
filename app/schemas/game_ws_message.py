from typing import Any, Literal

from pydantic import BaseModel
from services.score_calculator.enums.enums import Wind, Yaku

ActionType = Literal[
    "authenticateRequest",
    "authenticateResponse",
    "scoreCheckRequest",
    "scoreCheckResponse",
]


class BaseGameWebSocketMessage(BaseModel):
    action: ActionType
    data: dict[str, Any]

    class Config:
        extra = "forbid"


class AuthenticateData(BaseModel):
    access_token: str
    client_id: str


class AuthenticateResponseData(BaseModel):
    success: bool
    message: str
    client_id: str | None


class ScoreCheckData(BaseModel):
    hand: str
    winning_tile: str
    is_discarded: bool
    seat_wind: Wind
    round_wind: Wind
    is_last_tile_in_the_game: bool
    is_last_tile_of_its_kind: bool
    is_replacement_tile: bool
    is_robbing_the_kong: bool


class ScoreCheckResponseData(BaseModel):
    total_score: int
    yaku_score_list: list[tuple[Yaku, int]]


class AuthenticateRequestMessage(BaseGameWebSocketMessage):
    action: Literal["authenticateRequest"]
    data: AuthenticateData


class AuthenticateResponseMessage(BaseGameWebSocketMessage):
    action: Literal["authenticateResponse"]
    data: AuthenticateResponseData


class ScoreCheckRequestMessage(BaseGameWebSocketMessage):
    action: Literal["scoreCheckRequest"]
    data: ScoreCheckData


class ScoreCheckResponseMessage(BaseGameWebSocketMessage):
    action: Literal["scoreCheckRequest"]
    data: ScoreCheckResponseData


GameWebSocketMessage = (
    AuthenticateRequestMessage
    | AuthenticateResponseMessage
    | ScoreCheckRequestMessage
    | ScoreCheckResponseMessage
)
