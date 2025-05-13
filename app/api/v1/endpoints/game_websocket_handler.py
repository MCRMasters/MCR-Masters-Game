# app/api/v1/endpoints/game_websocket_handler.py

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import WebSocket, status
from starlette.websockets import WebSocketDisconnect

from app.core.error import MCRDomainError
from app.core.room_manager import RoomManager
from app.schemas.ws import MessageEventType, WSMessage
from app.services.game_manager.manager import GameManager
from app.services.game_manager.models.enums import AbsoluteSeat, GameTile
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.types import ActionType, GameEventType

logger = logging.getLogger(__name__)


class GameWebSocketHandler:
    def __init__(
        self,
        websocket: WebSocket,
        game_id: int,
        room_manager: RoomManager,
        user_id: str,
        user_nickname: str,
    ):
        self.websocket: WebSocket = websocket
        self.game_id: int = game_id
        self.room_manager: RoomManager = room_manager
        self.user_id: str = user_id
        self.user_nickname: str = user_nickname

    async def handle_connection(self) -> bool:
        try:
            await self.room_manager.connect(
                websocket=self.websocket,
                game_id=self.game_id,
                user_id=self.user_id,
                user_nickname=self.user_nickname,
            )
            await self._notify_user_joined()
            await self.handle_messages()
        except MCRDomainError as e:
            await self.websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=str(e),
            )
            return False
        except WebSocketDisconnect:
            await self.handle_disconnection()
            return False
        except Exception as e:
            await self.handle_error(e)
            return False
        return True

    async def handle_messages(self) -> None:
        while True:
            try:
                data = await self.websocket.receive_json()
                message = WSMessage(
                    event=data.get("event", ""),
                    data=data.get("data", {}),
                )
            except WebSocketDisconnect:
                break
            except (ValueError, TypeError) as e:
                await self.websocket.send_json(
                    WSMessage(
                        event=MessageEventType.ERROR,
                        data={"message": f"Invalid message format: {e}"},
                    ).model_dump(),
                )
                continue

            message_handlers: dict[
                MessageEventType,
                Callable[[WSMessage], Coroutine[Any, Any, None]],
            ] = {
                MessageEventType.PING: self.handle_ping,
                MessageEventType.GAME_EVENT: self.handle_game_event,
                MessageEventType.RETURN_ACTION: self.handle_return_action,
                MessageEventType.EMOJI_SEND: self.handle_emoji,
                MessageEventType.REQUEST_RELOAD: self.handle_reload,
            }
            handler = message_handlers.get(message.event)
            if handler:
                await handler(message)
            else:
                await self.websocket.send_json(
                    WSMessage(
                        event=MessageEventType.ERROR,
                        data={"message": f"Unknown event: {message.event}"},
                    ).model_dump(),
                )

    async def handle_reload(self, message: WSMessage) -> None:  # noqa : ARG002
        game_manager = self.room_manager.game_managers[self.game_id]
        await game_manager.round_manager.send_reload_data(uid=self.user_id)

    async def handle_emoji(self, message: WSMessage) -> None:
        try:
            game_manager = self.room_manager.game_managers[self.game_id]

            emoji_key = message.data.get("emoji_key")
            if emoji_key is None:
                await self.send_error("Missing emoji_key in emoji message.")
                return

            player_index = game_manager.player_uid_to_index.get(self.user_id)
            if player_index is None:
                await self.send_error("User not registered in game manager.")
                return

            if game_manager.round_manager.player_index_to_seat:
                player_seat = game_manager.round_manager.player_index_to_seat[
                    player_index
                ]
            else:
                player_seat = AbsoluteSeat(player_index)
            msg = WSMessage(
                event=MessageEventType.EMOJI_BROADCAST,
                data={
                    "emoji_key": emoji_key,
                    "seat": player_seat,
                },
            )
            await game_manager.network_service.broadcast(
                message=msg.model_dump(),
                game_id=game_manager.game_id,
                exclude_user_id=self.user_id,
            )
        except Exception as e:
            await self.send_error(f"Error processing emoji broadcast: {e}")

    async def handle_return_action(self, message: WSMessage) -> None:
        try:
            _action_type = message.data.get("action_type")
            if _action_type is None:
                await self.send_error(
                    "Missing 'action_type' field in return action message.",
                )
                return
            action_type: ActionType = ActionType(_action_type)
            _action_tile = message.data.get("action_tile")
            if _action_tile is None:
                await self.send_error(
                    "Missing 'action_tile' field in return action message.",
                )
                return
            action_tile: GameTile = GameTile(_action_tile)
            action_id: int = message.data.get("action_id", -1)

            game_manager: GameManager = self.room_manager.game_managers[self.game_id]
            player_index: int | None = game_manager.player_uid_to_index.get(
                self.user_id,
            )
            if player_index is None:
                await self.send_error("User not registered in game manager.")
                return
            player_seat: AbsoluteSeat
            if game_manager.round_manager.player_index_to_seat:
                player_seat = game_manager.round_manager.player_index_to_seat[
                    player_index
                ]
            else:
                player_seat = AbsoluteSeat(player_index)

            event_type: GameEventType | None = (
                GameEventType.create_from_action_type_except_kan(
                    action_type=action_type,
                )
            )
            if action_type == ActionType.KAN:
                event_type = game_manager.round_manager.hands[
                    player_seat
                ].get_kan_event_type_from_tile(
                    tile=action_tile,
                    is_discarded=game_manager.round_manager.winning_conditions.is_discarded,
                )
            if event_type is None:
                await self.send_error("Invalid action")
                return

            game_event = GameEvent(
                event_type=event_type,
                player_seat=player_seat,
                action_id=action_id,
                data={"tile": action_tile},
            )

            is_valid: bool = await game_manager.is_valid_event(
                event=game_event,
            )
            if is_valid:
                await self.send_success("Game event received")
            else:
                await self.send_error("Game event is invalid")
        except Exception as e:
            await self.send_error(f"Error processing return action: {e}")

    async def handle_game_event(self, message: WSMessage) -> None:
        try:
            game_manager = self.room_manager.game_managers[self.game_id]

            event_type_value = message.data.get("event_type")
            if event_type_value is None:
                await self.send_error("Missing event_type in game event message.")
                return

            event_type = GameEventType(int(event_type_value))

            action_id = message.data.get("action_id", -1)

            player_index = game_manager.player_uid_to_index.get(self.user_id)
            if player_index is None:
                await self.send_error("User not registered in game manager.")
                return

            if game_manager.round_manager.player_index_to_seat:
                player_seat = game_manager.round_manager.player_index_to_seat[
                    player_index
                ]
            else:
                player_seat = AbsoluteSeat(player_index)

            event_payload: dict[str, Any] = message.data.get("data", {})

            new_event = GameEvent(
                event_type=event_type,
                player_seat=player_seat,
                action_id=action_id,
                data=event_payload,
            )

            is_valid: bool = await game_manager.is_valid_event(
                event=new_event,
            )
            if is_valid:
                await self.send_success("Game event received")
            else:
                await self.send_error("Game event is invalid")
                await game_manager.round_manager.send_reload_data(uid=self.user_id)
        except Exception as e:
            await self.send_error(f"Error processing game event: {e}")

    async def send_success(self, success_message: str) -> None:
        success_msg = WSMessage(
            event=MessageEventType.SUCCESS,
            data={"message": success_message},
        )
        await self.room_manager.send_personal_message(
            message=success_msg.model_dump(),
            game_id=self.game_id,
            user_id=self.user_id,
        )

    async def send_error(self, message: str) -> None:
        error_response = WSMessage(
            event=MessageEventType.ERROR,
            data={"message": message},
        ).model_dump()
        await self.room_manager.send_personal_message(
            error_response,
            self.game_id,
            self.user_id,
        )

    async def handle_ping(self, _: WSMessage) -> None:
        await self.room_manager.send_personal_message(
            WSMessage(
                event=MessageEventType.PONG,
                data={"message": "pong"},
            ).model_dump(),
            self.game_id,
            self.user_id,
        )

    async def handle_disconnection(self) -> None:
        await self.room_manager.disconnect(game_id=self.game_id, user_id=self.user_id)

    async def handle_error(self, e: Exception) -> None:
        logger.error("GameWebSocketHandler: WebSocket error: %s", e, exc_info=True)
        if self.websocket.client_state.CONNECTED:
            await self.websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason=str(e),
            )

    async def _notify_user_joined(self) -> None:
        response = WSMessage(
            event=MessageEventType.USER_JOINED,
            data={"user_id": self.user_id},
        )
        await self.room_manager.broadcast(
            message=response.model_dump(),
            game_id=self.game_id,
            exclude_user_id=self.user_id,
        )
