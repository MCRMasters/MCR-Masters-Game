from collections import Counter
from dataclasses import dataclass

from app.services.game_manager.models.call_block import CallBlock
from app.services.game_manager.models.enums import GameTile


@dataclass
class GameHand:
    tiles: Counter[GameTile]
    call_blocks: list[CallBlock]
    tsumo_tile: GameTile | None = None
