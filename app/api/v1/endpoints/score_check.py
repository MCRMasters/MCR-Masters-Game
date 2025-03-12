from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from app.schemas.score_check_input import ScoreCheckInput
from app.schemas.score_check_response import ScoreCheckResponse, YakuScore
from app.services.score_calculator.enums.enums import Tile
from app.services.score_calculator.score_calculator import ScoreCalculator
from tests.test_utils import (
    create_default_winning_conditions,
    name_to_tile,
    raw_string_to_hand_class,
)

router = APIRouter()


@router.get("/score-check-test", response_class=HTMLResponse)
def read_score_check_test() -> str:
    base_dir = Path(__file__).resolve().parent
    html_path = base_dir / "score_check.html"
    return html_path.read_text(encoding="utf-8")


@router.post("/score-check", response_model=ScoreCheckResponse)
def score_check(input: ScoreCheckInput) -> ScoreCheckResponse:
    hand = raw_string_to_hand_class(input.raw_hand)
    if (winning_tile := name_to_tile(input.winning_tile)) == Tile.F0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid winning_tile: {input.winning_tile}",
        )
    try:
        seat_wind = input.seat_wind
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid seat_wind: {input.seat_wind}",
        )
    try:
        round_wind = input.round_wind
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid round_wind: {input.round_wind}",
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

    return ScoreCheckResponse(
        total_score=score_calc.result.total_score,
        yaku_score_list=[
            YakuScore(name=yaku.name, score=score)
            for yaku, score in score_calc.result.yaku_score_list
        ],
    )
