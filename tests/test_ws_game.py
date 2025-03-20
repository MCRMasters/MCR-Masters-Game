import pytest
from fastapi.testclient import TestClient

from app.dependencies.room_manager import get_room_manager
from app.main import app


class DummyRoomManager:
    def __init__(self, game_id: int):
        self.game_id = game_id
        self.websocket = None

    async def generate_game_id(self) -> int:
        return self.game_id

    async def connect(self, websocket, game_id: int, user_id, user_nickname: str):
        self.websocket = websocket

    async def disconnect(self, game_id: int, user_id):
        pass

    async def broadcast(self, message, game_id: int, exclude_user_id=None):
        pass

    async def send_personal_message(self, message, game_id: int, user_id):
        pass


@pytest.mark.parametrize(
    "hostname, port, dummy_game_id, expected_ws_url",
    [
        ("localhost", 8000, 123, "ws://localhost:8000/api/v1/games/123"),
        ("example.com", 80, 456, "ws://example.com/api/v1/games/456"),
        ("127.0.0.1", 8080, 789, "ws://127.0.0.1:8080/api/v1/games/789"),
    ],
)
def test_start_game(hostname, port, dummy_game_id, expected_ws_url):
    app.dependency_overrides[get_room_manager] = lambda: DummyRoomManager(dummy_game_id)
    client = TestClient(app)
    client.base_url = f"http://{hostname}:{port}"
    response = client.post("/api/v1/games/start")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["websocket_url"] == expected_ws_url
    app.dependency_overrides.pop(get_room_manager, None)
