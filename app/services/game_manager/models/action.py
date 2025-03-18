from __future__ import annotations

from dataclasses import dataclass

from app.services.game_manager.models.enums import GameTile, RelativeSeat
from app.services.game_manager.models.types import ActionType


@dataclass(order=True)
class Action:
    type: ActionType
    seat_priority: RelativeSeat
    tile: GameTile
