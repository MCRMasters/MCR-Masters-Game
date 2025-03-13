from dataclasses import dataclass

from app.services.game_manager.models.enums import ActionType, Seat


@dataclass(order=True)
class Action:
    type: ActionType
    seat_priority: Seat
