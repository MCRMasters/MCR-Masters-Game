from __future__ import annotations

import asyncio
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
    ) -> None:
        self.websocket: WebSocket = websocket
        self.game_id: int = game_id
        self.room_manager: RoomManager = room_manager
        self.user_id: str = user_id
        self.user_nickname: str = user_nickname

        self._msg_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self._recv_task: asyncio.Task[None] | None = None
        self._proc_task: asyncio.Task[None] | None = None

        self._send_lock: asyncio.Lock = asyncio.Lock()

    def _rethrow_if_exception(self, task: asyncio.Task) -> None:
        """Check a task for an exception and re-raise it."""
        if exc := task.exception():
            raise exc

    async def handle_connection(self) -> bool:
        try:
            await self.room_manager.connect(
                websocket=self.websocket,
                game_id=self.game_id,
                user_id=self.user_id,
                user_nickname=self.user_nickname,
            )
            await self._notify_user_joined()

            self._recv_task = asyncio.create_task(self._recv_loop())
            self._proc_task = asyncio.create_task(self._proc_loop())

            done, _ = await asyncio.wait(
                {self._recv_task, self._proc_task},
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for task in done:
                self._rethrow_if_exception(task)
        except MCRDomainError as exc:
            await self._close_ws(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
            return False
        except WebSocketDisconnect:
            await self.handle_disconnection()
            return False
        except Exception as exc:
            await self.handle_error(exc)
            return False
        finally:
            try:
                await self.handle_disconnection()
            except Exception:
                logger.debug(
                    "handle_disconnection failed for %s:%d",
                    self.user_id,
                    self.game_id,
                )

        return True

    async def _recv_loop(self) -> None:
        try:
            while True:
                try:
                    data = await self.websocket.receive_json()
                    await self._msg_queue.put(data)
                except WebSocketDisconnect:
                    break
                except WebSocketDisconnect:
                    break
                except Exception as exc:
                    logger.debug("recv_loop got exception: %s", exc)
                    break
        finally:
            await self._msg_queue.put(None)

    async def _proc_loop(self) -> None:
        while True:
            msg_dict = await self._msg_queue.get()
            if msg_dict is None:
                break
            await self._handle_message(msg_dict)

    async def _handle_message(self, raw: dict[str, Any]) -> None:
        try:
            message = WSMessage(
                event=raw.get("event", ""),
                data=raw.get("data", {}),
            )
        except (ValueError, TypeError) as exc:
            await self._send_error(f"Invalid message format: {exc}")
            return

        dispatch: dict[
            MessageEventType,
            Callable[[WSMessage], Coroutine[Any, Any, None]],
        ] = {
            MessageEventType.PING: self._handle_ping,
            MessageEventType.GAME_EVENT: self._handle_game_event,
            MessageEventType.RETURN_ACTION: self._handle_return_action,
            MessageEventType.EMOJI_SEND: self._handle_emoji,
            MessageEventType.REQUEST_RELOAD: self._handle_reload,
        }
        handler = dispatch.get(message.event)
        if handler is None:
            await self._send_error(f"Unknown event: {message.event}")
            return
        await handler(message)

    async def _handle_reload(self, message: WSMessage) -> None:  # noqa : ARG002
        game_manager = self.room_manager.game_managers[self.game_id]
        await game_manager.round_manager.send_reload_data(uid=self.user_id)

    async def _handle_emoji(self, message: WSMessage) -> None:
        try:
            game_manager = self.room_manager.game_managers[self.game_id]
            emoji_key = message.data.get("emoji_key")
            if emoji_key is None:
                await self._send_error("Missing emoji_key in emoji message.")
                return

            player_index = game_manager.player_uid_to_index.get(self.user_id)
            if player_index is None:
                await self._send_error("User not registered in game manager.")
                return

            if game_manager.round_manager.player_index_to_seat:
                player_seat = game_manager.round_manager.player_index_to_seat[
                    player_index
                ]
            else:
                player_seat = AbsoluteSeat(player_index)

            msg = WSMessage(
                event=MessageEventType.EMOJI_BROADCAST,
                data={"emoji_key": emoji_key, "seat": player_seat},
            )
            await game_manager.network_service.broadcast(
                message=msg.model_dump(),
                game_id=game_manager.game_id,
                exclude_user_id=self.user_id,
            )
        except Exception as exc:
            await self._send_error(f"Error processing emoji broadcast: {exc}")

    async def _handle_return_action(self, message: WSMessage) -> None:
        try:
            _action_type = message.data.get("action_type")
            if _action_type is None:
                await self._send_error(
                    "Missing 'action_type' field in return action message.",
                )
                return
            action_type: ActionType = ActionType(_action_type)

            _action_tile = message.data.get("action_tile")
            if _action_tile is None:
                await self._send_error(
                    "Missing 'action_tile' field in return action message.",
                )
                return
            action_tile: GameTile = GameTile(_action_tile)

            action_id: int = message.data.get("action_id", -1)
            game_manager: GameManager = self.room_manager.game_managers[self.game_id]

            player_index = game_manager.player_uid_to_index.get(self.user_id)
            if player_index is None:
                await self._send_error("User not registered in game manager.")
                return

            player_seat: AbsoluteSeat
            if game_manager.round_manager.player_index_to_seat:
                player_seat = game_manager.round_manager.player_index_to_seat[
                    player_index
                ]
            else:
                player_seat = AbsoluteSeat(player_index)

            event_type: GameEventType | None = (
                GameEventType.create_from_action_type_except_kan(action_type)
            )
            if action_type == ActionType.KAN:
                event_type = game_manager.round_manager.hands[
                    player_seat
                ].get_kan_event_type_from_tile(
                    tile=action_tile,
                    is_discarded=game_manager.round_manager.winning_conditions.is_discarded,
                )
            if event_type is None:
                logger.debug(
                    "Invalid Person's Hand %s",
                    game_manager.round_manager.hands[player_seat],
                )
                await self._send_error("Invalid action")
                return

            game_event = GameEvent(
                event_type=event_type,
                player_seat=player_seat,
                action_id=action_id,
                data={"tile": action_tile},
            )

            is_valid: bool = await game_manager.is_valid_event(game_event)
            if is_valid:
                await self._send_success("Game event received")
            else:
                logger.debug(
                    "Invalid Person's Hand %s",
                    game_manager.round_manager.hands[player_seat],
                )
                await self._send_error("Game event is invalid")
        except Exception as exc:
            await self._send_error(f"Error processing return action: {exc}")

    async def _handle_game_event(self, message: WSMessage) -> None:
        try:
            game_manager = self.room_manager.game_managers[self.game_id]
            event_type_value = message.data.get("event_type")
            if event_type_value is None:
                await self._send_error("Missing event_type in game event message.")
                return
            event_type = GameEventType(int(event_type_value))
            action_id = message.data.get("action_id", -1)

            player_index = game_manager.player_uid_to_index.get(self.user_id)
            if player_index is None:
                await self._send_error("User not registered in game manager.")
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

            is_valid = await game_manager.is_valid_event(new_event)
            if is_valid:
                await self._send_success("Game event received")
            else:
                logger.debug(
                    "Invalid Person's Hand %s",
                    game_manager.round_manager.hands[player_seat],
                )
                await self._send_error("Game event is invalid")
                if not game_manager._check_action_id(event=new_event):
                    await game_manager.round_manager.send_reload_data(uid=self.user_id)
        except Exception as exc:
            await self._send_error(f"Error processing game event: {exc}")

    async def _send_success(self, success_message: str) -> None:
        msg = WSMessage(
            event=MessageEventType.SUCCESS,
            data={"message": success_message},
        )
        await self.room_manager.send_personal_message(
            msg.model_dump(),
            self.game_id,
            self.user_id,
        )

    async def _send_error(self, error_message: str) -> None:
        msg = WSMessage(event=MessageEventType.ERROR, data={"message": error_message})
        await self.room_manager.send_personal_message(
            msg.model_dump(),
            self.game_id,
            self.user_id,
        )

    async def _handle_ping(self, _: WSMessage) -> None:
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

    async def handle_error(self, exc: Exception) -> None:
        logger.error("GameWebSocketHandler: WebSocket error: %s", exc, exc_info=True)
        await self._close_ws(code=status.WS_1011_INTERNAL_ERROR, reason=str(exc))

    async def _close_ws(self, *, code: int, reason: str) -> None:
        async with self._send_lock:
            if self.websocket.client_state.CONNECTED:
                await self.websocket.close(code=code, reason=reason)

    async def _notify_user_joined(self) -> None:
        response = WSMessage(
            event=MessageEventType.USER_JOINED,
            data={"user_id": self.user_id},
        )
        await self.room_manager.broadcast(
            response.model_dump(),
            self.game_id,
            exclude_user_id=self.user_id,
        )
