import heapq
from collections import Counter
from typing import Final

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.enums import GameTile, Round, Seat, Wind
from app.services.game_manager.models.player import Player
from app.services.game_manager.models.winning_conditions import GameWinningConditions
from app.services.score_calculator.hand.hand import Hand


class RoundManager:
    def __init__(self) -> None:
        self.tile_deck: list[GameTile] = []
        self.hand_list: list[Hand] = []
        self.kawa_list: list[list[GameTile]] = [
            [] for _ in range(GameManager.MAX_PLAYERS)
        ]
        self.visible_tiles_count: Counter[GameTile] = Counter()
        self.winning_conditions: GameWinningConditions
        self.tile_draw_index_left: int = 0
        self.tile_draw_index_right: int = GameManager.TOTAL_TILES
        self.wind_to_index: dict[Wind, int] = {}
        self.action_id: int = 0
        self.action_manager: ActionManager


class GameManager:
    def __init__(self, player_list: list[Player]):
        self.player_list: list[Player] = player_list
        self.round_manager: RoundManager
        self.current_round: Round = Round.E1

    MINIMUM_HU_SCORE: Final[int] = 8
    TOTAL_TILES: Final[int] = 144
    MAX_PLAYERS: Final[int] = 4


class ActionManager:
    def __init__(self, action_list: list[Action]):
        self.action_heap: list[Action] = action_list
        heapq.heapify(self.action_heap)
        self.selected_action_heap: list[Action] = []
        self.finished_players: set[Seat] = set()
        self.final_action: Action | None = None

    def empty(self) -> bool:
        return not self.action_heap

    def push_action(self, action: Action) -> Action | None:
        if self.final_action:
            return self.final_action
        heapq.heappush(self.selected_action_heap, action)
        self.finished_players.add(action.seat_priority)
        while (
            self.action_heap
            and self.action_heap[0].seat_priority in self.finished_players
        ):
            top_action: Action = heapq.heappop(self.action_heap)
            if top_action == self.selected_action_heap[0]:
                self.final_action = top_action
                break
        return self.final_action
