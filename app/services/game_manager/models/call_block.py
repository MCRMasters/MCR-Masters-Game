from __future__ import annotations

from dataclasses import dataclass

from app.services.game_manager.models.enums import AbsoluteSeat, GameTile, RelativeSeat
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.types import CallBlockType, GameEventType


@dataclass
class CallBlock:
    type: CallBlockType
    first_tile: GameTile
    source_seat: RelativeSeat
    source_tile_index: int = 0

    @staticmethod
    def create_from_game_event(
        game_event: GameEvent,
        current_seat: AbsoluteSeat,
        source_tile: GameTile,
    ) -> CallBlock:
        first_tile: GameTile | None = game_event.data.get("tile", None)
        if first_tile is None:
            raise ValueError("No tile in game event")
        match game_event.event_type:
            case GameEventType.SHOMIN_KAN:
                return CallBlock(
                    type=CallBlockType.SHOMIN_KONG,
                    first_tile=first_tile,
                    source_seat=RelativeSeat.create_from_absolute_seats(
                        current_seat=game_event.player_seat,
                        target_seat=current_seat,
                    ),
                )
            case GameEventType.DAIMIN_KAN:
                return CallBlock(
                    type=CallBlockType.DAIMIN_KONG,
                    first_tile=first_tile,
                    source_seat=RelativeSeat.create_from_absolute_seats(
                        current_seat=game_event.player_seat,
                        target_seat=current_seat,
                    ),
                )
            case GameEventType.AN_KAN:
                return CallBlock(
                    type=CallBlockType.AN_KONG,
                    first_tile=first_tile,
                    source_seat=RelativeSeat.create_from_absolute_seats(
                        current_seat=game_event.player_seat,
                        target_seat=current_seat,
                    ),
                )
            case GameEventType.PON:
                return CallBlock(
                    type=CallBlockType.PUNG,
                    first_tile=first_tile,
                    source_seat=RelativeSeat.create_from_absolute_seats(
                        current_seat=game_event.player_seat,
                        target_seat=current_seat,
                    ),
                )
            case GameEventType.CHII:
                return CallBlock(
                    type=CallBlockType.CHII,
                    first_tile=first_tile,
                    source_seat=RelativeSeat.create_from_absolute_seats(
                        current_seat=game_event.player_seat,
                        target_seat=current_seat,
                    ),
                    source_tile_index=source_tile - first_tile,
                )
            case _:
                raise ValueError("Can't convert to ")
