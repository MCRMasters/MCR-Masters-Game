from dataclasses import dataclass, field
from typing import Any

from app.services.game_manager.models.enums import AbsoluteSeat
from app.services.game_manager.models.types import GameEventType


@dataclass
class GameEvent:
    event_type: GameEventType
    player_seat: AbsoluteSeat
    action_id: int
    data: dict[str, Any] = field(default_factory=dict)
