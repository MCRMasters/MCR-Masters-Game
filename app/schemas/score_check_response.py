from pydantic import BaseModel


class YakuScore(BaseModel):
    name: str
    score: int


class ScoreCheckResponse(BaseModel):
    total_score: int
    yaku_score_list: list[YakuScore]
