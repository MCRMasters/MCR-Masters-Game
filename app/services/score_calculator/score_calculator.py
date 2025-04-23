from collections import Counter
from copy import deepcopy

from app.services.score_calculator.block.block import Block
from app.services.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.services.score_calculator.divide.honors_and_knitted_shape import (
    can_divide_honors_and_knitted_shape,
)
from app.services.score_calculator.divide.seven_pairs_shape import (
    divide_seven_pairs_shape,
)
from app.services.score_calculator.divide.thirteen_orphans_shape import (
    can_divide_thirteen_orphans_shape,
)
from app.services.score_calculator.enums.enums import BlockType, Tile, Yaku
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.result.result import (
    BlockRelationScoringContext,
    ScoreResult,
)
from app.services.score_calculator.tenpai_calculator import get_tenpai_tiles
from app.services.score_calculator.utility.utility import (
    EXCLUDED_YAKUS,
    YAKU_POINT,
    YAKUS_INCLUDING_PUNG_OF_TOH,
)
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)
from app.services.score_calculator.yaku_check.blocks_yaku_checker import (
    BlocksYakuChecker,
)
from app.services.score_calculator.yaku_check.hand_yaku_checker import HandYakuChecker
from app.services.score_calculator.yaku_check.winning_conditions_yaku_checker import (
    WinningConditionsYakuChecker,
)


class ScoreCalculator:
    def __init__(self, hand: Hand, winning_conditions: WinningConditions):
        self.hand: Hand = hand
        self.winning_conditions: WinningConditions = winning_conditions
        self._highest_result = ScoreResult(yaku_score_list=[])
        self.is_blocks_divided = False
        if self.hand.tiles[Tile.F0] > 0:
            return
        tenpai_hand = deepcopy(hand)
        tenpai_hand.tiles[self.winning_conditions.winning_tile] -= 1
        self.winning_conditions.count_tenpai_tiles = len(
            get_tenpai_tiles(
                tenpai_hand=tenpai_hand,
            ),
        )

        self._calculate()

    @property
    def result(self) -> ScoreResult:
        return self._highest_result

    def _calculate(self) -> None:
        self._calculate_honors_and_knitted_shape_score()
        if not self.is_blocks_divided:
            self._calculate_thirteen_orphans_shape_score()
        if not self.is_blocks_divided:
            self._calculate_general_and_seven_pairs_shape_score()

        if self.is_blocks_divided and self._highest_result.total_score == 0:
            self._highest_result.add_yaku(yaku=Yaku.ChickenHand, count=1)

    def _calculate_general_and_seven_pairs_shape_score(self) -> None:
        parsed_hands: list[list[Block]] = (
            divide_general_shape(self.hand)
            + divide_general_shape_knitted_sub(self.hand)
            + divide_seven_pairs_shape(self.hand)
        )
        if parsed_hands:
            self.is_blocks_divided = True
        for blocks in parsed_hands:
            score_result = self._calculate_score_result(blocks=blocks, yaku_list=[])
            self._highest_result = max(self._highest_result, score_result)

    def _calculate_thirteen_orphans_shape_score(self) -> None:
        if can_divide_thirteen_orphans_shape(self.hand):
            self.is_blocks_divided = True
            yaku_list: list[Yaku] = [Yaku.ThirteenOrphans]

            score_result = self._calculate_score_result(blocks=[], yaku_list=yaku_list)
            self._highest_result = max(self._highest_result, score_result)

    def _calculate_honors_and_knitted_shape_score(self) -> None:
        if can_divide_honors_and_knitted_shape(self.hand):
            self.is_blocks_divided = True
            yaku_list: list[Yaku] = []

            honor_count = sum(1 for tile in Tile.honor_tiles() if self.hand.tiles[tile])
            if honor_count == 7:
                yaku_list.append(Yaku.GreaterHonorsAndKnittedTiles)
            elif honor_count == 5:
                yaku_list.extend(
                    [Yaku.LesserHonorsAndKnittedTiles, Yaku.KnittedStraight],
                )
            else:
                yaku_list.append(Yaku.LesserHonorsAndKnittedTiles)

            score_result = self._calculate_score_result(blocks=[], yaku_list=yaku_list)
            self._highest_result = max(self._highest_result, score_result)

    def _calculate_score_result(
        self,
        blocks: list[Block],
        yaku_list: list[Yaku],
    ) -> ScoreResult:
        scoring_context: BlockRelationScoringContext = (
            BlockRelationScoringContext.create_from_blocks(
                blocks=[
                    deepcopy(block) for block in blocks if block.type != BlockType.PAIR
                ],
            )
        )
        if blocks:
            yaku_list += HandYakuChecker(
                blocks=deepcopy(blocks),
                winning_conditions=deepcopy(self.winning_conditions),
            ).yakus
        if len(blocks) == 5:
            yaku_list += BlocksYakuChecker(blocks=deepcopy(blocks)).yakus
            yaku_list += scoring_context.get_yakus()
        if len(blocks) == 7 and len({block.tile.type for block in blocks}):
            yaku_list += [Yaku.AllTypes]
        yaku_list += WinningConditionsYakuChecker(
            blocks=deepcopy(blocks),
            winning_conditions=deepcopy(self.winning_conditions),
        ).yakus

        yaku_dict = self._process_yaku_exclusions(yaku_list)

        score_result: ScoreResult = ScoreResult(yaku_score_list=[])
        for yaku, count in yaku_dict.items():
            score_result.add_yaku(yaku, count)
        # 사귀일 예외처리
        if (
            not (
                Yaku.QuadrupleChow in yaku_dict
                or (
                    Yaku.SevenPairs in yaku_dict
                    and (Yaku.AllTerminals in yaku_dict or Yaku.AllGreen in yaku_dict)
                )
            )
            and (
                tile_hog_count := self.hand.tiles.count(4)
                - sum(1 for block in self.hand.call_blocks if block.is_quad)
            )
            > 0
        ):
            score_result.add_yaku(Yaku.TileHog, tile_hog_count)

        # 요구각 예외처리
        pung_count: int = self._count_pung_of_terminals_and_honors(
            scoring_context,
            yaku_dict,
        )
        if pung_count > 0:
            score_result.add_yaku(Yaku.PungOfTerminalsOrHonors, pung_count)
        return score_result

    def _process_yaku_exclusions(self, yaku_list: list[Yaku]) -> Counter[Yaku]:
        yaku_counter = Counter(yaku_list)
        sorted_yaku = sorted(yaku_counter, key=lambda y: -YAKU_POINT[y])
        for yaku in sorted_yaku:
            for excluded in EXCLUDED_YAKUS.get(yaku, []):
                yaku_counter.pop(excluded, None)
        return yaku_counter

    def _check_skip_block(self, block: Block, yaku_counter: Counter[Yaku]) -> bool:
        return block.is_dragon or (
            block.is_wind
            and (
                Yaku.LittleFourWinds in yaku_counter
                or Yaku.BigThreeWinds in yaku_counter
                or block.tile
                in {
                    self.winning_conditions.round_wind,
                    self.winning_conditions.seat_wind,
                }
            )
        )

    def _count_pung_of_terminals_and_honors(
        self,
        scoring_context: BlockRelationScoringContext,
        yaku_counter: Counter[Yaku],
    ) -> int:
        if any(yaku in yaku_counter for yaku in YAKUS_INCLUDING_PUNG_OF_TOH):
            return 0
        return sum(
            1
            for block in scoring_context.blocks
            if (block.is_outside and block.is_pung)
            and not self._check_skip_block(block, yaku_counter)
        )
