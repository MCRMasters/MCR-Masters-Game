from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import WebSocket, status
from starlette.websockets import WebSocketDisconnect

from app.core.error import MCRDomainError
from app.core.room_manager import RoomManager
from app.schemas.ws import GameWebSocketActionType, WebSocketMessage, WebSocketResponse


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
        finally:
            await self.room_manager.disconnect(
                game_id=self.game_id,
                user_id=self.user_id,
            )
        return True

    async def handle_messages(self) -> None:
        while True:
            try:
                data = await self.websocket.receive_json()
                message = WebSocketMessage(
                    action=data.get("action", ""),
                    data=data.get("data"),
                )
            except Exception as e:
                await self.websocket.send_json(
                    WebSocketResponse(
                        status="error",
                        action=GameWebSocketActionType.ERROR,
                        error=f"Invalid message format: {e}",
                    ).model_dump(),
                )
                continue
            message_handlers: dict[
                GameWebSocketActionType,
                Callable[[WebSocketMessage], Coroutine[Any, Any, None]],
            ] = {
                GameWebSocketActionType.PING: self.handle_ping,
            }
            handler = message_handlers.get(message.action)
            if handler:
                await handler(message)
            else:
                await self.websocket.send_json(
                    WebSocketResponse(
                        status="error",
                        action=GameWebSocketActionType.ERROR,
                        error=f"Unknown action: {message.action}",
                    ).model_dump(),
                )

    async def send_error(self, message: str) -> None:
        error_response = WebSocketResponse(
            status="error",
            action=GameWebSocketActionType.ERROR,
            data={"message": message},
        ).model_dump()
        await self.room_manager.send_personal_message(
            error_response,
            self.game_id,
            self.user_id,
        )

    async def handle_ping(self, _: WebSocketMessage) -> None:
        await self.room_manager.send_personal_message(
            WebSocketResponse(
                status="success",
                action=GameWebSocketActionType.PONG,
                data={"message": "pong"},
            ).model_dump(),
            self.game_id,
            self.user_id,
        )

    async def handle_disconnection(self) -> None:
        await self.room_manager.disconnect(game_id=self.game_id, user_id=self.user_id)

    async def handle_error(self, e: Exception) -> None:
        print(f"[GameWebSocketHandler] WebSocket error: {e}")
        if self.websocket.client_state.CONNECTED:
            await self.websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason=str(e),
            )

    async def _notify_user_joined(self) -> None:
        response = WebSocketResponse(
            status="success",
            action=GameWebSocketActionType.USER_JOINED,
            data={"user_id": str(self.user_id)},
        )
        await self.room_manager.broadcast(
            message=response.model_dump(),
            game_id=self.game_id,
            exclude_user_id=self.user_id,
        )
