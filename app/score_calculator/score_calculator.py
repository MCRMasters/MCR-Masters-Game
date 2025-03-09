from copy import deepcopy

from app.score_calculator.block.block import Block
from app.score_calculator.divide.general_shape import divide_general_shape
from app.score_calculator.enums.enums import BlockType, Yaku
from app.score_calculator.hand.hand import Hand
from app.score_calculator.result.result import ScoreResult, ScoringContext
from app.score_calculator.tenpai_calculator import get_tenpai_tiles
from app.score_calculator.utility.utility import (
    EXCLUDED_YAKUS,
    YAKU_POINT,
    YAKUS_INCLUDING_PUNG_OF_TOH,
)
from app.score_calculator.winning_conditions.winning_conditions import WinningConditions
from app.score_calculator.yaku_check.blocks_yaku_checker import BlocksYakuChecker
from app.score_calculator.yaku_check.hand_yaku_checker import HandYakuChecker
from app.score_calculator.yaku_check.winning_conditions_yaku_checker import (
    WinningConditionsYakuChecker,
)


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
        self.highest_result = ScoreResult(yaku_score_list=[])
        self.is_blocks_divided = False

    def general_shape_calculator(self) -> None:
        parsed_hands: list[list[Block]] = divide_general_shape(self.hand)
        if parsed_hands:
            self.is_blocks_divided = True
        for blocks in parsed_hands:
            score_result = self._calculate_score_result(blocks)
            self.highest_result = max(self.highest_result, score_result)

    def _calculate_score_result(self, blocks: list[Block]) -> ScoreResult:
        scoring_context: ScoringContext = ScoringContext.create_from_blocks(
            blocks=[
                deepcopy(block) for block in blocks if block.type != BlockType.PAIR
            ],
        )

        yaku_list: list[Yaku] = []
        yaku_list += HandYakuChecker(
            blocks=deepcopy(blocks),
            winning_conditions=deepcopy(self.winning_conditions),
        ).yakus
        yaku_list += BlocksYakuChecker(blocks=deepcopy(blocks)).yakus
        yaku_list += scoring_context.get_yakus()
        yaku_list += WinningConditionsYakuChecker(
            blocks=deepcopy(blocks),
            winning_conditions=deepcopy(self.winning_conditions),
        ).yakus

        yaku_set = self._process_yaku_exclusions(yaku_list)

        score_result: ScoreResult = ScoreResult(yaku_score_list=[])
        for yaku in yaku_set:
            score_result.add_yaku(yaku, 1)

        if not (
            Yaku.SevenPairs in yaku_set
            and (Yaku.AllTerminals in yaku_set or Yaku.AllGreen in yaku_set)
        ):
            score_result.add_yaku(
                Yaku.TileHog,
                self.hand.tiles.count(4)
                - sum(1 for block in self.hand.call_blocks if block.is_quad),
            )

        pung_count: int = self._count_pung_of_terminals_and_honors(
            scoring_context,
            yaku_set,
        )
        score_result.add_yaku(Yaku.PungOfTerminalsOrHonors, pung_count)
        return score_result

    def _process_yaku_exclusions(self, yaku_list: list[Yaku]) -> set[Yaku]:
        yaku_set = set(yaku_list)
        yaku_list.sort(key=lambda y: -YAKU_POINT[y])
        for yaku in yaku_list:
            if yaku in yaku_set:
                for excluded_yaku in EXCLUDED_YAKUS[yaku]:
                    yaku_set.discard(excluded_yaku)
        return yaku_set

    def _count_pung_of_terminals_and_honors(
        self,
        scoring_context: ScoringContext,
        yaku_set: set[Yaku],
    ) -> int:
        count = 0
        if any(yaku in yaku_set for yaku in YAKUS_INCLUDING_PUNG_OF_TOH):
            for block in scoring_context.blocks:
                if not (block.is_outside and block.is_pung):
                    continue
                if block.is_dragon or (
                    block.is_wind
                    and (
                        Yaku.LittleFourWinds in yaku_set
                        or block.tile
                        in {
                            self.winning_conditions.round_wind,
                            self.winning_conditions.seat_wind,
                        }
                    )
                ):
                    continue
                count += 1
        return count
