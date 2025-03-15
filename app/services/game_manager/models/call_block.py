from dataclasses import dataclass

from app.services.game_manager.models.enums import GameTile, RelativeSeat
from app.services.game_manager.models.types import CallBlockType


@dataclass
class CallBlock:
    type: CallBlockType
    first_tile: GameTile
    source_tile_index: int
    source_seat: RelativeSeat
