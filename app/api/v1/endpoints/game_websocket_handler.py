from uuid import UUID

from fastapi import WebSocket, status
from pydantic import ValidationError
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
        user_id: UUID,
        user_nickname: str,
    ):
        self.websocket: WebSocket = websocket
        self.game_id: int = game_id
        self.room_manager: RoomManager = room_manager

        self.user_id: UUID = user_id
        self.user_nickname: str = user_nickname

    async def handle_connection(self) -> bool:
        try:
            # room manager에 등록
            await self.room_manager.connect(
                websocket=self.websocket,
                game_id=self.game_id,
                user_id=self.user_id,
                user_nickname=self.user_nickname,
            )

            # 연결 알림
            await self._notify_user_joined()

            # 메시지 처리 루프
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
            # 예외/연결종료 등으로 빠져나올 때 정리
            if self.game_id and self.user_id:
                self.room_manager.disconnect(game_id=self.game_id, user_id=self.user_id)

        return True

    async def handle_messages(self):
        while True:
            data = await self.websocket.receive_json()
            try:
                message = WebSocketMessage(
                    action=data.get("action", ""),
                    data=data.get("data"),
                )
            except ValidationError as e:
                await self.websocket.send_json(
                    WebSocketResponse(
                        status="error",
                        action=GameWebSocketActionType.ERROR,
                        error=f"Invalid message format: {e}",
                    ).model_dump(),
                )
                continue

            # 메시지 액션별 처리
            message_handlers = {
                GameWebSocketActionType.PING: self.handle_ping,
                # 필요하다면 추가 액션: DRAW, DISCARD 등...
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

    async def handle_ping(self, _: WebSocketMessage):
        """PING 요청에 대한 PONG 응답"""
        await self.room_manager.send_personal_message(
            WebSocketResponse(
                status="success",
                action=GameWebSocketActionType.PONG,
                data={"message": "pong"},
            ).model_dump(),
            self.game_id,
            self.user_id,
        )

    async def handle_disconnection(self):
        """연결 해제 처리"""
        # 연결 해제에 따른 게임 상태 업데이트 등
        self.room_manager.disconnect(game_id=self.game_id, user_id=self.user_id)
        # 다른 유저에게 알림
        await self._notify_user_left()

    async def handle_error(self, e: Exception):
        """내부 에러 처리"""
        print(f"[GameWebSocketHandler] WebSocket error: {e}")
        if self.websocket.client_state.CONNECTED:
            await self.websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason=str(e),
            )

    async def _notify_user_joined(self):
        """
        특정 유저가 게임에 들어왔음을 브로드캐스트 하는 예시
        """
        response = WebSocketResponse(
            status="success",
            action=GameWebSocketActionType.USER_JOINED,
            data={"user_id": str(self.user_id)},
        )
        await self.room_manager.broadcast(
            response.model_dump(),
            self.game_id,
            exclude_user_id=self.user_id,
        )

    async def _notify_user_left(self):
        """
        특정 유저가 게임에서 나갔음을 브로드캐스트 하는 예시
        """
        response = WebSocketResponse(
            status="success",
            action=GameWebSocketActionType.USER_LEFT,
            data={"user_id": str(self.user_id)},
        )
        await self.room_manager.broadcast(
            message=response.model_dump(),
            game_id=self.game_id,
        )
