# tests/test_watch_endpoint.py

from collections import deque
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.v1.endpoints.watch import get_room_manager, router
from app.core.room_manager import RoomManager
from app.schemas.ws import MessageEventType


@pytest.fixture
def rm():
    return RoomManager()


@pytest.fixture
def app(rm: RoomManager):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_room_manager] = lambda: rm
    return app


@pytest.fixture
def client(app: FastAPI):
    return TestClient(app)


def test_watch_not_started(client: TestClient):
    with client.websocket_connect("/games/1/watch") as ws:  # noqa : SIM117
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()


def test_watch_wait_remaining(client: TestClient, rm: RoomManager):
    now = datetime.now(UTC)
    rm.game_start_times[1] = now - timedelta(minutes=2)

    with client.websocket_connect("/games/1/watch") as ws:
        data = ws.receive_json()
        assert data["event"] == MessageEventType.WAIT_REMAINING
        remaining = data["data"]["remaining_time"]
        assert 0 < remaining <= 180

        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()


def test_watch_after_snapshot(client: TestClient, rm: RoomManager):
    now = datetime.now(UTC)
    rm.game_start_times[1] = now - timedelta(minutes=6)

    snapshot_msg = {"event": MessageEventType.WATCH_RELOAD_DATA, "data": {"foo": 1}}
    too_new_msg = {"event": MessageEventType.WATCH_RELOAD_DATA, "data": {"foo": 2}}
    hist = rm.watch_history.setdefault(1, deque())
    hist.append((now - timedelta(minutes=7), snapshot_msg))
    hist.append((now - timedelta(minutes=4), too_new_msg))

    with client.websocket_connect("/games/1/watch") as ws:
        data = ws.receive_json()
        assert data == snapshot_msg

        ws.close()
