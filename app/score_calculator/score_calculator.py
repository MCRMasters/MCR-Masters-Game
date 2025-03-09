from copy import deepcopy

from app.score_calculator.hand.hand import Hand
from app.score_calculator.result.result import ScoreResult
from app.score_calculator.tenpai_calculator import get_tenpai_tiles
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions


class ScoreCalculator:
    def __init__(self, hand: Hand, winning_conditions: WinningConditions):
        self.hand: Hand = hand
        self.winning_conditions: WinningConditions = winning_conditions
        tenpai_hand = deepcopy(hand)
        tenpai_hand.tiles[self.winning_conditions.winning_tile] -= 1
        self.winning_conditions.count_tenpai_tiles = len(
            get_tenpai_tiles(
                tenpai_hand=tenpai_hand,
            ),
        )
        self.highest_result = ScoreResult(yaku_score_list=[], tenpai_tiles=[])
