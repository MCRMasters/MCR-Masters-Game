from pydantic import BaseModel

from app.services.score_calculator.enums.enums import Wind


class ScoreCheckInput(BaseModel):
    raw_hand: str
    winning_tile: str
    is_discarded: bool
    seat_wind: Wind = Wind.EAST
    round_wind: Wind = Wind.EAST
    is_last_tile_in_the_game: bool = False
    is_last_tile_of_its_kind: bool = False
    is_replacement_tile: bool = False
    is_robbing_the_kong: bool = False
