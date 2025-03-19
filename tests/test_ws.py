import asyncio
from uuid import UUID, uuid4

import pytest

from app.api.v1.endpoints.game_websocket_handler import GameWebSocketHandler
from app.schemas.ws import GameWebSocketActionType


class DummyWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.receive_queue = asyncio.Queue()
        self.client_state = type("DummyState", (), {"CONNECTED": True})()

    async def send_json(self, message):
        self.sent_messages.append(message)

    async def receive_json(self):
        return await self.receive_queue.get()

    async def close(self, code, reason):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


class DummyRoomManager:
    def __init__(self):
        self.websocket = None
        self.sent_messages = []

    async def connect(self, websocket, game_id: int, user_id: UUID, user_nickname: str):
        self.websocket = websocket

    async def disconnect(self, game_id: int, user_id: UUID):
        pass

    async def send_personal_message(self, message, game_id: int, user_id: UUID):
        self.sent_messages.append(message)
        await self.websocket.send_json(message)

    async def broadcast(
        self,
        message,
        game_id: int,
        exclude_user_id: UUID | None = None,
    ):
        self.sent_messages.append(message)


@pytest.mark.asyncio
async def test_handle_ping():
    dummy_ws = DummyWebSocket()
    dummy_rm = DummyRoomManager()
    await dummy_rm.connect(dummy_ws, game_id=1, user_id=uuid4(), user_nickname="Tester")
    user_id = uuid4()
    handler = GameWebSocketHandler(
        websocket=dummy_ws,
        game_id=1,
        room_manager=dummy_rm,
        user_id=user_id,
        user_nickname="Tester",
    )
    await handler.handle_ping(None)
    assert dummy_rm.sent_messages, "No message sent via room manager"
    response = dummy_rm.sent_messages[-1]
    assert response["status"] == "success"
    assert response["action"] == GameWebSocketActionType.PONG
    assert response["data"].get("message") == "pong"


@pytest.mark.asyncio
async def test_unknown_action():
    dummy_ws = DummyWebSocket()
    dummy_rm = DummyRoomManager()
    await dummy_rm.connect(dummy_ws, game_id=1, user_id=uuid4(), user_nickname="Tester")
    user_id = uuid4()
    handler = GameWebSocketHandler(
        websocket=dummy_ws,
        game_id=1,
        room_manager=dummy_rm,
        user_id=user_id,
        user_nickname="Tester",
    )
    invalid_message = {"action": "invalid", "data": {}}
    await dummy_ws.receive_queue.put(invalid_message)
    task = asyncio.create_task(handler.handle_messages())
    await asyncio.sleep(0.1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert dummy_ws.sent_messages, "No response sent by handler"
    response = dummy_ws.sent_messages[-1]
    assert response["status"] == "error"
    assert response["action"] == "error"
    assert (
        "validation error" in response["error"].lower()
        or "unknown action" in response["error"].lower()
    )


@pytest.mark.asyncio
async def test_handle_connection_success():
    dummy_ws = DummyWebSocket()
    dummy_rm = DummyRoomManager()
    user_id = uuid4()
    handler = GameWebSocketHandler(
        websocket=dummy_ws,
        game_id=1,
        room_manager=dummy_rm,
        user_id=user_id,
        user_nickname="Tester",
    )

    async def one_message_handle_messages(self):
        try:
            data = await asyncio.wait_for(self.websocket.receive_json(), timeout=1)
            if data.get("action") == "ping":
                await self.handle_ping(None)
        except TimeoutError:
            pass

    handler.handle_messages = one_message_handle_messages.__get__(
        handler,
        GameWebSocketHandler,
    )
    task = asyncio.create_task(handler.handle_connection())
    await asyncio.sleep(0.1)
    await dummy_ws.receive_queue.put({"action": "ping", "data": {}})
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert dummy_rm.sent_messages, "No ping response sent."
    response = dummy_rm.sent_messages[-1]
    assert response["status"] == "success"
    assert response["action"] == GameWebSocketActionType.PONG
    assert response["data"].get("message") == "pong"
