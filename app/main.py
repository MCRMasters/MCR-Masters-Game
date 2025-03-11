import os

from fastapi import FastAPI, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.score_calculator.enums.enums import Tile, Wind
from app.score_calculator.score_calculator import ScoreCalculator
from tests.test_utils import (
    create_default_winning_conditions,
    name_to_tile,
    raw_string_to_hand_class,
)

app = FastAPI()


class ScoreCheckInput(BaseModel):
    raw_hand: str
    winning_tile: str
    is_discarded: bool
    seat_wind: str = Wind.EAST.name
    round_wind: str = Wind.EAST.name
    is_last_tile_in_the_game: bool = False
    is_last_tile_of_its_kind: bool = False
    is_replacement_tile: bool = False
    is_robbing_the_kong: bool = False


@app.get("/", response_class=HTMLResponse)
def read_root() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "index.html")
    with open(html_path, encoding="utf-8") as f:
        return f.read()


@app.post("/score-check")
def score_check(input: ScoreCheckInput) -> JSONResponse:
    hand = raw_string_to_hand_class(input.raw_hand)
    if (winning_tile := name_to_tile(input.winning_tile)) == Tile.F0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid winning_tile: {input.winning_tile}"},
        )
    try:
        seat_wind = Wind[input.seat_wind]
    except KeyError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid seat_wind: {input.seat_wind}"},
        )
    try:
        round_wind = Wind[input.round_wind]
    except KeyError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid round_wind: {input.round_wind}"},
        )

    winning_conditions = create_default_winning_conditions(
        winning_tile=winning_tile,
        is_discarded=input.is_discarded,
        seat_wind=seat_wind,
        round_wind=round_wind,
        is_last_tile_in_the_game=input.is_last_tile_in_the_game,
        is_last_tile_of_its_kind=input.is_last_tile_of_its_kind,
        is_replacement_tile=input.is_replacement_tile,
        is_robbing_the_kong=input.is_robbing_the_kong,
    )

    score_calc = ScoreCalculator(hand=hand, winning_conditions=winning_conditions)
    score_calc._general_and_seven_pairs_shape_calculator()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "total_score": score_calc.highest_result.total_score,
            "yaku_score_list": [
                {"name": yaku.name, "score": score}
                for yaku, score in score_calc.highest_result.yaku_score_list
            ],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
