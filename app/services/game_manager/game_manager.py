from __future__ import annotations

import asyncio
import contextlib
import logging
from random import shuffle
from typing import Final

import httpx

from app.core.config import settings
from app.core.network_service import NetworkService
from app.schemas.ws import MessageEventType, WSMessage
from app.services.game_manager.fsm.round_fsm import FlowerState, WaitingNextRoundState
from app.services.game_manager.models.action import Action
from app.services.game_manager.models.enums import GameTile, Round
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.player import Player, PlayerData
from app.services.game_manager.models.types import GameEventType
from app.services.game_manager.round_manager import RoundManager

logger = logging.getLogger(__name__)


class GameManager:
    MINIMUM_HU_SCORE: Final[int] = 8
    MAX_PLAYERS: Final[int] = 4
    TOTAL_ROUNDS: Final[int] = 16

    def __init__(
        self,
        game_id: int,
        network_service: NetworkService,
    ) -> None:
        self.game_id: int = game_id
        self.network_service: NetworkService = network_service
        self.player_list: list[Player]
        self.player_uid_to_index: dict[str, int]
        self.round_manager: RoundManager
        self.current_round: Round
        self.action_id: int
        self.event_queue: asyncio.Queue[GameEvent]
        self.event_queue_lock: asyncio.Lock
        self._reload_task: asyncio.Task | None = None

    def init_game(self, players_data: list[PlayerData]) -> None:
        if len(players_data) != self.MAX_PLAYERS:
            raise ValueError(
                f"[GameManager] {self.MAX_PLAYERS} players needed, "
                f"{len(players_data)} players received",
            )
        self.player_list = []
        self.player_uid_to_index = {}
        shuffle(players_data)
        for index, player_data in enumerate(players_data):
            self.player_list.append(
                Player.create_from_received_data(
                    player_data=player_data,
                    index=index,
                ),
            )
            self.player_uid_to_index[player_data.uid] = index
        self.round_manager = RoundManager(self)
        self.current_round = Round.E1
        self.action_id = 0
        self.event_queue = asyncio.Queue()
        self.event_queue_lock = asyncio.Lock()

    async def start_game(self) -> None:
        self._reload_task = asyncio.create_task(self._reload_loop())

        start_msg = WSMessage(
            event=MessageEventType.GAME_START_INFO,
            data={
                "players": [
                    {
                        "uid": player.uid,
                        "nickname": player.nickname,
                        "index": player.index,
                        "score": player.score,
                    }
                    for player in self.player_list
                ],
            },
        )
        await self.network_service.broadcast(
            message=start_msg.model_dump(),
            game_id=self.game_id,
        )

        try:
            for _ in range(self.TOTAL_ROUNDS):
                await self.round_manager.run_round()
                self.current_round = self.current_round.next_round
        finally:
            if self._reload_task:
                self._reload_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._reload_task

        await self.submit_game_result()

    async def send_init_game_data(self, uid: str) -> None:
        start_msg = WSMessage(
            event=MessageEventType.GAME_START_INFO,
            data={
                "players": [
                    {
                        "uid": player.uid,
                        "nickname": player.nickname,
                        "index": player.index,
                        "score": player.score,
                    }
                    for player in self.player_list
                ],
            },
        )
        await self.network_service.send_personal_message(
            message=start_msg.model_dump(),
            game_id=self.game_id,
            user_id=uid,
        )

    async def _reload_loop(self) -> None:
        while True:
            try:
                await self.round_manager.send_watch_reload_data()
            except Exception as e:
                logger.error("reload loop error: %s", e, exc_info=True)
            await asyncio.sleep(1)

    async def submit_game_result(self) -> None:
        scores: list[int] = [p.score for p in self.player_list]
        msg = WSMessage(
            event=MessageEventType.END_GAME,
            data={
                "players_score": scores,
            },
        )
        await self.network_service.broadcast(
            message=msg.model_dump(),
            game_id=self.game_id,
        )
        endpoint = f"https://{settings.COER_SERVER_URL}/internal/game-server/rooms/{self.game_id}/end-game"
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.post(endpoint)
                resp.raise_for_status()
                logger.debug("[GameManager] end-game 요청 성공: %s", resp.json())
            except httpx.HTTPError as exc:
                logger.debug("[GameManager] end-game 요청 실패: %s", exc)
            finally:
                await self.network_service.end_all_connection(game_id=self.game_id)

    def increase_action_id(self) -> None:
        self.action_id += 1

    async def add_event(self, event: GameEvent) -> None:
        async with self.event_queue_lock:
            if event.action_id >= 0 and event.action_id != self.action_id:
                logger.debug(
                    "[GameManager.add_event] Ignored event with mismatched "
                    f"action_id: {event.action_id} (expected {self.action_id})",
                )
                return
            await self.event_queue.put(event)
            logger.debug(f"[GameManager.add_event] Event added: {event}")

    async def is_valid_event(self, event: GameEvent) -> bool:
        if not self._check_action_id(event):
            return False
        handler = {
            GameEventType.SKIP: self._handle_skip,
            GameEventType.CHII: self._handle_action_event,
            GameEventType.PON: self._handle_action_event,
            GameEventType.HU: self._handle_action_event,
            GameEventType.FLOWER: self._handle_action_event,
            GameEventType.AN_KAN: self._handle_action_event,
            GameEventType.DAIMIN_KAN: self._handle_action_event,
            GameEventType.SHOMIN_KAN: self._handle_action_event,
            GameEventType.DISCARD: self._handle_discard,
            GameEventType.INIT_FLOWER_OK: self._handle_init_flower_ok,
            GameEventType.NEXT_ROUND_CONFIRM: self._handle_next_round_confirm,
        }.get(event.event_type, self._handle_default)

        return await handler(event)

    def _check_action_id(self, event: GameEvent) -> bool:
        if event.action_id < 0 or event.action_id == self.action_id:
            return True
        logger.debug(f"invalid action id: action id: {self.action_id}, event {event}")
        return False

    async def _handle_skip(self, event: GameEvent) -> bool:
        rm = self.round_manager
        if event.action_id != self.action_id:
            return False
        valid = (
            rm.current_player_seat == event.player_seat
            or rm.winning_conditions.is_discarded
            or rm.winning_conditions.is_robbing_the_kong
        )
        if valid and rm.current_player_seat != event.player_seat:
            await self.add_event(event=event)
        return valid

    async def _handle_action_event(self, event: GameEvent) -> bool:
        choice = Action.create_from_game_event(
            game_event=event,
            current_player_seat=self.round_manager.current_player_seat,
        )
        valid = choice in self.round_manager.action_choices
        if valid:
            await self.add_event(event=event)
        return valid

    async def _handle_discard(self, event: GameEvent) -> bool:
        return await self._handle_discard_validate(event=event)

    async def _handle_init_flower_ok(self, event: GameEvent) -> bool:
        valid = self.round_manager.is_current_state_instance(FlowerState)
        if valid:
            await self.add_event(event=event)
        return valid

    async def _handle_next_round_confirm(self, event: GameEvent) -> bool:
        valid = self.round_manager.is_current_state_instance(WaitingNextRoundState)
        if valid:
            await self.add_event(event=event)
        return valid

    async def _handle_default(self, event: GameEvent) -> bool:
        event
        return False

    async def _handle_discard_validate(self, event: GameEvent) -> bool:
        if not event.data or "tile" not in event.data:
            return False
        try:
            tile_int = int(event.data["tile"])
            tile = GameTile(tile_int)
        except (ValueError, TypeError):
            return False
        if event.action_id != self.action_id:
            return False
        hand = self.round_manager.hands[event.player_seat]
        if hand.tiles.get(tile, 0) < 1:
            return False
        msg = WSMessage(
            event=MessageEventType.DISCARD,
            data={
                "tile": tile,
                "seat": event.player_seat,
                "is_tsumogiri": event.data["is_tsumogiri"],
            },
        )
        await self.network_service.broadcast(
            message=msg.model_dump(),
            game_id=self.game_id,
        )
        await self.add_event(event)
        return True
