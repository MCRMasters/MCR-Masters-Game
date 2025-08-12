from __future__ import annotations

import heapq

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.enums import RelativeSeat
from app.services.game_manager.models.types import ActionType


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
        """
        새로운 Action을 push하고, 최종 선택된 우선순위 높은 valid Action을 반환

        Args:
            action (Action): 추가할 Action

        Returns:
            Action | None: 최종 Action (없으면 None)
        """
        if self.final_action:
            return self.final_action
        if action.type != ActionType.SKIP:
            heapq.heappush(self.selected_action_heap, action)
        self.finished_players.add(action.seat_priority)
        while (
            self.action_heap
            and self.selected_action_heap
            and self.action_heap[0].seat_priority in self.finished_players
        ):
            top_action: Action = heapq.heappop(self.action_heap)
            if top_action == self.selected_action_heap[0]:
                self.final_action = top_action
                break
        return self.final_action
