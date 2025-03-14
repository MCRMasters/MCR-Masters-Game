from __future__ import annotations

import heapq
from collections import Counter
from random import shuffle
from typing import Final

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.deck import Deck
from app.services.game_manager.models.enums import GameTile, RelativeSeat, Round, Wind
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.player import Player, PlayerDataReceived
from app.services.game_manager.models.winning_conditions import GameWinningConditions


class RoundManager:
    def __init__(self, game_manager: GameManager) -> None:
        self.game_manager: GameManager = game_manager
        self.tile_deck: Deck
        self.hand_list: list[GameHand]
        self.kawa_list: list[list[GameTile]]
        self.visible_tiles_count: Counter[GameTile]
        self.winning_conditions: GameWinningConditions
        self.wind_to_player_index: dict[Wind, int] = {}
        self.action_manager: ActionManager | None

    def init_round(self) -> None:
        self.tile_deck = Deck()
        self.hand_list = [
            GameHand.create_from_tiles(self.tile_deck.draw_haipai())
            for _ in range(GameManager.MAX_PLAYERS)
        ]
        self.kawa_list = [[] for _ in range(GameManager.MAX_PLAYERS)]
        self.visible_tiles_count = Counter()
        self.winning_conditions = GameWinningConditions.create_default_conditions()
        self.action_manager = None


class GameManager:
    MINIMUM_HU_SCORE: Final[int] = 8
    MAX_PLAYERS: Final[int] = 4

    def __init__(self) -> None:
        self.player_list: list[Player]
        self.round_manager: RoundManager
        self.current_round: Round
        self.action_id: int

    def init_game(self, player_datas: list[PlayerDataReceived]) -> None:
        if len(player_datas) != GameManager.MAX_PLAYERS:
            raise ValueError(
                f"[GameManager] {GameManager.MAX_PLAYERS} players needed, "
                f"{len(player_datas)} players received",
            )
        self.player_list = []
        index_mapping: list[int] = list(range(GameManager.MAX_PLAYERS))
        shuffle(index_mapping)
        for i, player_data in enumerate(player_datas):
            self.player_list.append(
                Player.create_from_received_data(
                    player_data=player_data,
                    index=index_mapping[i],
                ),
            )

        self.round_manager = RoundManager(self)
        self.round_manager.init_round()
        self.current_round = Round.E1
        self.action_id = 0


class ActionManager:
    def __init__(self, action_list: list[Action]):
        self.action_heap: list[Action] = action_list
        heapq.heapify(self.action_heap)
        self.selected_action_heap: list[Action] = []
        self.finished_players: set[RelativeSeat] = set()
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
