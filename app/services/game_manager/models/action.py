from __future__ import annotations

from dataclasses import dataclass

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile, RelativeSeat
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.types import ActionType


@dataclass(order=True)
class Action:
    type: ActionType
    seat_priority: RelativeSeat
    tile: GameTile

    @staticmethod
    def create_from_game_event(
        game_event: GameEvent,
        current_player_seat: AbsoluteSeat,
    ) -> Action:
        tile: GameTile = GameTile.F0
        if (received_tile := game_event.data.get("tile", None)) is not None:
            tile = received_tile
        action_type: ActionType | None = ActionType.create_from_game_event_type(
            game_event_type=game_event.event_type,
        )
        if action_type is None:
            raise ValueError("action type is None.")
        return Action(
            type=action_type,
            seat_priority=RelativeSeat.create_from_absolute_seats(
                current_seat=current_player_seat,
                target_seat=game_event.player_seat,
            ),
            tile=tile,
        )
