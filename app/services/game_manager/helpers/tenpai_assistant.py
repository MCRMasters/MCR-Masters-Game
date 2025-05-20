from collections import Counter
from copy import deepcopy

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.winning_conditions import GameWinningConditions
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.result.result import (
    ScoreResult,
)
from app.services.score_calculator.score_calculator import ScoreCalculator
from app.services.score_calculator.tenpai_calculator import get_tenpai_tiles
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)


class TenpaiAssistant:
    def __init__(
        self,
        game_hand: GameHand,
        game_winning_conditions: GameWinningConditions,
        visible_tiles_count: Counter[GameTile],
        seat_wind: AbsoluteSeat,
        round_wind: AbsoluteSeat,
    ):
        self.game_hand = deepcopy(game_hand)
        self.winning_conditions = WinningConditions.create_from_game_winning_conditions(
            game_winning_conditions=game_winning_conditions,
            seat_wind=seat_wind,
            round_wind=round_wind,
        )
        self.visible_tiles_count = deepcopy(visible_tiles_count)

    def get_score_result_from_game_infos(
        self,
        hand: Hand,
        winning_conditions: WinningConditions,
    ) -> ScoreResult:
        return ScoreCalculator(
            hand=hand,
            winning_conditions=winning_conditions,
        ).result

    def _evaluate_tenpai_tiles(
        self,
        tenpai_hand: Hand,
        working_winning_conditions: WinningConditions,
        visible_tiles: Counter[GameTile],
    ) -> dict[GameTile, tuple[ScoreResult, ScoreResult]]:
        result: dict[GameTile, tuple[ScoreResult, ScoreResult]] = {}
        tenpai_tiles = get_tenpai_tiles(tenpai_hand=tenpai_hand)
        if not tenpai_tiles:
            return result
        working_winning_conditions.count_tenpai_tiles = len(tenpai_tiles)
        working_winning_conditions.is_replacement_tile = False
        working_winning_conditions.is_robbing_the_kong = False
        working_winning_conditions.is_last_tile_in_the_game = False
        for tenpai_tile in tenpai_tiles:
            if tenpai_hand.tiles[tenpai_tile] >= 4:
                continue
            tenpai_hand.tiles[tenpai_tile] += 1
            working_winning_conditions.winning_tile = tenpai_tile

            working_winning_conditions.is_last_tile_of_its_kind = (
                visible_tiles[GameTile(tenpai_tile)] >= 3
            )
            working_winning_conditions.is_discarded = False
            tsumo_score = self.get_score_result_from_game_infos(
                hand=tenpai_hand,
                winning_conditions=working_winning_conditions,
            )
            working_winning_conditions.is_discarded = True
            discard_score = self.get_score_result_from_game_infos(
                hand=tenpai_hand,
                winning_conditions=working_winning_conditions,
            )
            tenpai_hand.tiles[tenpai_tile] -= 1
            result[GameTile(tenpai_tile)] = (tsumo_score, discard_score)
        return result

    def get_tenpai_assistance_info_with_tenpai_hand(
        self,
        tenpai_game_hand: GameHand,
    ) -> dict[GameTile, tuple[ScoreResult, ScoreResult]]:
        tenpai_hand = Hand.create_from_game_hand(hand=deepcopy(tenpai_game_hand))
        return self._evaluate_tenpai_tiles(
            tenpai_hand=tenpai_hand,
            working_winning_conditions=deepcopy(self.winning_conditions),
            visible_tiles=deepcopy(self.visible_tiles_count),
        )

    def get_tenpai_assistance_info_in_full_hand(
        self,
    ) -> dict[GameTile, dict[GameTile, tuple[ScoreResult, ScoreResult]]]:
        result: dict[GameTile, dict[GameTile, tuple[ScoreResult, ScoreResult]]] = {}
        for discard_tile in self.game_hand.tiles:
            tenpai_game_hand = deepcopy(self.game_hand)
            tenpai_game_hand.apply_discard(discard_tile)
            if tenpai_game_hand.has_flower:
                continue
            visible_tiles = deepcopy(self.visible_tiles_count)
            visible_tiles[discard_tile] += 1
            sub_info = self._evaluate_tenpai_tiles(
                tenpai_hand=Hand.create_from_game_hand(hand=tenpai_game_hand),
                working_winning_conditions=deepcopy(self.winning_conditions),
                visible_tiles=visible_tiles,
            )
            if sub_info:
                result[discard_tile] = sub_info
        return result
