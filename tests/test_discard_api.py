import pytest

from app.api.v1.endpoints.game_websocket_handler import GameWebSocketHandler
from app.schemas.ws import GameWebSocketActionType, WebSocketMessage
from app.services.game_manager.models.enums import GameTile


class FakeGameManager:
    def get_valid_discard_result(self, uid: str, tile: GameTile) -> dict[str, str]:
        if int(tile) == 1:
            return {"seat": "EAST"}
        return {}


class FakeRoomManager:
    def __init__(self):
        self.sent_personal_messages: list[tuple[dict, int, str]] = []
        self.broadcast_messages: list[tuple[dict, int, str | None]] = []
        self.game_managers: dict[int, FakeGameManager] = {}

    async def send_personal_message(
        self,
        message: dict,
        game_id: int,
        user_id: str,
    ) -> None:
        self.sent_personal_messages.append((message, game_id, user_id))

    async def broadcast(
        self,
        message: dict,
        game_id: int,
        exclude_user_id: str | None = None,
    ) -> None:
        self.broadcast_messages.append((message, game_id, exclude_user_id))


class FakeWebSocket:
    def __init__(self):
        self.sent_messages: list[dict] = []

    async def send_json(self, message: dict) -> None:
        self.sent_messages.append(message)


@pytest.fixture
def fake_environment():
    fake_ws = FakeWebSocket()
    fake_room_manager = FakeRoomManager()
    fake_game_manager = FakeGameManager()
    game_id = 100
    fake_room_manager.game_managers[game_id] = fake_game_manager
    user_id = "user123"
    user_nickname = "Tester"
    handler = GameWebSocketHandler(
        websocket=fake_ws,
        game_id=game_id,
        room_manager=fake_room_manager,
        user_id=user_id,
        user_nickname=user_nickname,
    )
    return handler, fake_ws, fake_room_manager


@pytest.mark.asyncio
async def test_handle_discard_no_tile(fake_environment):
    handler, _, fake_room_manager = fake_environment
    message = WebSocketMessage(action=GameWebSocketActionType.DISCARD, data={})
    await handler.handle_discard(message)
    assert fake_room_manager.sent_personal_messages, "An error message should be sent."
    err_msg, _, _ = fake_room_manager.sent_personal_messages[0]
    assert "No Tile" in err_msg.get("data", {}).get("message", "")


@pytest.mark.asyncio
async def test_handle_discard_tile_not_integer(fake_environment):
    handler, _, fake_room_manager = fake_environment
    message = WebSocketMessage(
        action=GameWebSocketActionType.DISCARD,
        data={"tile": "abc"},
    )
    await handler.handle_discard(message)
    assert fake_room_manager.sent_personal_messages, "An error message should be sent."
    err_msg, _, _ = fake_room_manager.sent_personal_messages[0]
    assert "Tile is not integer" in err_msg.get("data", {}).get("message", "")


@pytest.mark.asyncio
async def test_handle_discard_tile_invalid(fake_environment):
    handler, _, fake_room_manager = fake_environment
    message = WebSocketMessage(
        action=GameWebSocketActionType.DISCARD,
        data={"tile": 99},
    )
    await handler.handle_discard(message)
    assert fake_room_manager.sent_personal_messages, "An error message should be sent."
    err_msg, _, _ = fake_room_manager.sent_personal_messages[0]
    assert "Tile is not valid" in err_msg.get("data", {}).get("message", "")


@pytest.mark.asyncio
async def test_handle_discard_no_tile_in_hand(fake_environment):
    handler, _, fake_room_manager = fake_environment
    message = WebSocketMessage(action=GameWebSocketActionType.DISCARD, data={"tile": 2})
    await handler.handle_discard(message)
    assert fake_room_manager.sent_personal_messages, "An error message should be sent."
    err_msg, _, _ = fake_room_manager.sent_personal_messages[0]
    assert "No tile in hand" in err_msg.get("data", {}).get("message", "")


@pytest.mark.asyncio
async def test_handle_discard_success(fake_environment):
    handler, _, fake_room_manager = fake_environment
    message = WebSocketMessage(action=GameWebSocketActionType.DISCARD, data={"tile": 1})
    await handler.handle_discard(message)
    assert not fake_room_manager.sent_personal_messages, (
        "No personal error message should be sent."
    )
    assert fake_room_manager.broadcast_messages, "A broadcast message should be sent."
    broadcast_msg, _, _ = fake_room_manager.broadcast_messages[0]
    data = broadcast_msg.get("data", {})
    assert data.get("seat") == "EAST"
    assert data.get("tile") == 1
