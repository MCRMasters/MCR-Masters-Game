from __future__ import annotations

import asyncio
import heapq
import logging
import time
from collections import Counter
from collections.abc import Callable, Mapping
from contextlib import suppress
from copy import deepcopy
from random import shuffle
from typing import Any, Final

import httpx

from app.core.config import settings
from app.core.network_service import NetworkService
from app.schemas.ws import MessageEventType, WSMessage
from app.services.game_manager.fsm.round_fsm import (
    ActionState,
    DiscardState,
    DrawState,
    FlowerState,
    HuState,
    InitState,
    RobbingKongState,
    RoundState,
    TsumoState,
    WaitingNextRoundState,
)
from app.services.game_manager.helpers.tenpai_assistant import TenpaiAssistant
from app.services.game_manager.models.action import Action
from app.services.game_manager.models.call_block import CallBlock
from app.services.game_manager.models.deck import Deck
from app.services.game_manager.models.enums import (
    AbsoluteSeat,
    GameTile,
    RelativeSeat,
    Round,
)
from app.services.game_manager.models.event import GameEvent
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.player import (
    Player,
    PlayerData,
)
from app.services.game_manager.models.types import (
    ActionType,
    CallBlockType,
    GameEventType,
)
from app.services.game_manager.models.winning_conditions import (
    GameWinningConditions,
)
from app.services.score_calculator.enums.enums import Tile
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.result.result import ScoreResult
from app.services.score_calculator.score_calculator import ScoreCalculator
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)

logger = logging.getLogger(__name__)


class RoundManager:
    def __init__(self, game_manager: GameManager) -> None:
        self.game_manager: GameManager = game_manager
        self.tile_deck: Deck
        self.hands: list[GameHand]
        self.kawas: list[list[GameTile]]
        self.visible_tiles_count: Counter[GameTile]
        self.winning_conditions: GameWinningConditions
        self.seat_to_player_index: dict[AbsoluteSeat, int] = {}
        self.player_index_to_seat: dict[int, AbsoluteSeat] = {}
        self.action_manager: ActionManager | None
        self.current_player_seat: AbsoluteSeat
        self.action_choices: list[Action]
        self.action_choices_list: list[list[Action]]
        self.current_state: RoundState | None = None
        self.remaining_time: float = 0.0

    async def send_reload_data(self, uid: str) -> None:
        player_index = self.game_manager.player_uid_to_index[uid]
        player_seat = self.player_index_to_seat[player_index]

        player_list = self.game_manager.player_list

        hand = [t.value for t in self.hands[player_seat].tiles.elements()]

        hands_count = [
            sum(self.hands[i].tiles.values())
            for i in range(self.game_manager.MAX_PLAYERS)
        ]
        tsumo_tile = self.hands[player_seat].tsumo_tile
        tsumo_tiles_count = [
            1 if self.hands[i].tsumo_tile is not None else 0
            for i in range(self.game_manager.MAX_PLAYERS)
        ]
        flowers_count = [
            getattr(self.hands[i], "flower_point", 0)
            for i in range(self.game_manager.MAX_PLAYERS)
        ]

        raw_call_blocks = [
            deepcopy(self.hands[i].call_blocks)
            for i in range(self.game_manager.MAX_PLAYERS)
        ]
        for i, blocks in enumerate(raw_call_blocks):
            if AbsoluteSeat(i) != player_seat:
                for cb in blocks:
                    if cb.type == CallBlockType.AN_KONG:
                        cb.first_tile = GameTile.F0

        call_blocks_list = raw_call_blocks

        current_turn_seat = RelativeSeat.create_from_absolute_seats(
            current_seat=player_seat,
            target_seat=self.current_player_seat,
        )
        remaining_time = self.remaining_time
        tiles_remaining = self.tile_deck.tiles_remaining
        current_round = self.game_manager.current_round

        player = self.get_player_from_seat(seat=player_seat)
        msg = WSMessage(
            event=MessageEventType.RELOAD_DATA,
            data={
                "player_list": player_list,
                "hand": hand,
                "kawas": self.kawas,
                "action_id": self.game_manager.action_id,
                "action_choices_list": self.action_choices_list,
                "hands_count": hands_count,
                "tsumo_tile": tsumo_tile.value if tsumo_tile else None,
                "tsumo_tiles_count": tsumo_tiles_count,
                "flowers_count": flowers_count,
                "call_blocks_list": call_blocks_list,
                "current_turn_seat": current_turn_seat,
                "remaining_time": remaining_time,
                "tiles_remaining": tiles_remaining,
                "current_round": current_round,
            },
        )

        await self.game_manager.network_service.send_personal_message(
            message=msg.model_dump(),
            game_id=self.game_manager.game_id,
            user_id=player.uid,
        )

    async def run_round(self) -> None:
        self.current_state = InitState()
        while self.current_state is not None:
            self.current_state = await self.current_state.run(self)

    def is_current_state_instance(self, state_class: type[RoundState]) -> bool:
        if self.current_state is None:
            return False
        return isinstance(self.current_state, state_class)

    def init_round_data(self) -> None:
        self.tile_deck = Deck()
        # test deck
        # self.tile_deck.tiles = [0,0,0,1,2,3,4,5,6,7,8,8,8,
        #                         0,8,9,17,18,26,27,28,29,30,31,32,33,
        #                         1,2,10,11,12,20,21,22,7,7,7,33,33,
        #                         27,27,27,28,28,28,29,29,29,30,30,30,31,
        #                         0,0,0,0,27,27,27,27] + self.tile_deck.tiles
        self.hands = [
            GameHand.create_from_tiles(tiles=self.tile_deck.draw_haipai())
            for _ in range(self.game_manager.MAX_PLAYERS)
        ]
        self.hands[AbsoluteSeat.EAST].apply_tsumo(
            tile=self.tile_deck.draw_tiles(count=1)[0],
        )
        # TO BE REMOVED
        # self.tile_deck.tiles = (
        #     self.tile_deck.tiles[: self.tile_deck.draw_index_left]
        #     + [GameTile.F0] * 8
        #     + [GameTile.M1, GameTile.M2]
        #     + [GameTile.F1] * 8
        #     + [GameTile.M3, GameTile.M4]
        #     + self.tile_deck.tiles[
        #         (self.tile_deck.draw_index_left + 20) : (
        #             self.tile_deck.draw_index_right - 8
        #         )
        #     ]
        #     + [GameTile.F2] * 8
        #     + self.tile_deck.tiles[self.tile_deck.draw_index_right :]
        # )

        self.kawas = [[] for _ in range(self.game_manager.MAX_PLAYERS)]
        self.visible_tiles_count = Counter()
        self.winning_conditions = GameWinningConditions.create_default_conditions()
        self.init_seat_index_mapping()
        self.action_manager = None
        self.current_player_seat = AbsoluteSeat.EAST
        self.action_choices = []
        self.action_choices_list = []

    # Deal 1‥16 의 (index0,1,2,3) → 좌석 순서
    _DEAL_TABLE: Final[list[list[AbsoluteSeat]]] = [
        # idx0   idx1   idx2   idx3
        [
            AbsoluteSeat.EAST,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.WEST,
            AbsoluteSeat.NORTH,
        ],  # 1
        [
            AbsoluteSeat.NORTH,
            AbsoluteSeat.EAST,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.WEST,
        ],  # 2
        [
            AbsoluteSeat.WEST,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.EAST,
            AbsoluteSeat.SOUTH,
        ],  # 3
        [
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.WEST,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.EAST,
        ],  # 4
        [
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.EAST,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.WEST,
        ],  # 5
        [
            AbsoluteSeat.EAST,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.WEST,
            AbsoluteSeat.SOUTH,
        ],  # 6
        [
            AbsoluteSeat.NORTH,
            AbsoluteSeat.WEST,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.EAST,
        ],  # 7
        [
            AbsoluteSeat.WEST,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.EAST,
            AbsoluteSeat.NORTH,
        ],  # 8
        [
            AbsoluteSeat.NORTH,
            AbsoluteSeat.WEST,
            AbsoluteSeat.EAST,
            AbsoluteSeat.SOUTH,
        ],  # 9
        [
            AbsoluteSeat.WEST,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.EAST,
        ],  # 10
        [
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.EAST,
            AbsoluteSeat.WEST,
            AbsoluteSeat.NORTH,
        ],  # 11
        [
            AbsoluteSeat.EAST,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.WEST,
        ],  # 12
        [
            AbsoluteSeat.WEST,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.EAST,
        ],  # 13
        [
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.WEST,
            AbsoluteSeat.EAST,
            AbsoluteSeat.NORTH,
        ],  # 14
        [
            AbsoluteSeat.EAST,
            AbsoluteSeat.SOUTH,
            AbsoluteSeat.NORTH,
            AbsoluteSeat.WEST,
        ],  # 15
        [
            AbsoluteSeat.NORTH,
            AbsoluteSeat.EAST,
            AbsoluteSeat.WEST,
            AbsoluteSeat.SOUTH,
        ],  # 16
    ]

    def get_seat_mappings(
        self,
        deal: int,
    ) -> tuple[dict[AbsoluteSeat, int], dict[int, AbsoluteSeat]]:
        order = self._DEAL_TABLE[deal]

        seat_to_player = {seat: idx for idx, seat in enumerate(order)}
        player_to_seat = dict(enumerate(order))
        return seat_to_player, player_to_seat

    def init_seat_index_mapping(self) -> None:
        # 좌석 ↔ 플레이어 인덱스 매핑 생성
        self.seat_to_player_index, self.player_index_to_seat = self.get_seat_mappings(
            int(self.game_manager.current_round),
        )

    async def send_init_events(self) -> None:
        scores: list[int] = [p.score for p in self.game_manager.player_list]
        for seat in AbsoluteSeat:
            player: Player = self.get_player_from_seat(seat=seat)
            msg = WSMessage(
                event=MessageEventType.INIT_EVENT,
                data={
                    "player_seat": seat,
                    "players_score": scores,
                    "hand": list(self.hands[seat].tiles.elements()),
                    "tsumo_tile": self.hands[seat].tsumo_tile,
                },
            )
            await self.game_manager.network_service.send_personal_message(
                message=msg.model_dump(),
                game_id=self.game_manager.game_id,
                user_id=player.uid,
            )

    async def do_init_flower_action(self) -> None:
        new_tiles_list: list[list[GameTile]] = [
            [] for _ in range(self.game_manager.MAX_PLAYERS)
        ]
        applied_flowers_list: list[list[GameTile]] = [
            [] for _ in range(self.game_manager.MAX_PLAYERS)
        ]
        tsumo_tile_dict: dict[AbsoluteSeat, GameTile | None] = {}
        hand_dict: dict[AbsoluteSeat, list[GameTile]] = {}
        for seat in AbsoluteSeat:
            tsumo_tile_dict[seat] = self.hands[seat].tsumo_tile
            hand_dict[seat] = list(self.hands[seat].tiles.elements())
            while self.hands[seat].has_flower:
                if (applied_flower := self.hands[seat].apply_flower()) is None:
                    raise ValueError("Invalid hand value about flower tiles")
                applied_flowers_list[seat].append(applied_flower)
                new_tile: GameTile = self.tile_deck.draw_tiles_right(1)[0]
                self.hands[seat].apply_init_flower_tsumo(tile=new_tile)
                new_tiles_list[seat].append(new_tile)
        scores: list[int] = [p.score for p in self.game_manager.player_list]
        flower_count: list[int] = [hand.flower_point for hand in self.hands]
        for seat in AbsoluteSeat:
            data: dict[str, Any] = {
                "player_seat": seat,
                "players_score": scores,
                "hand": hand_dict[seat],
                "tsumo_tile": tsumo_tile_dict[seat],
                "new_tiles": new_tiles_list[seat],
                "applied_flowers": applied_flowers_list[seat],
                "flower_count": flower_count,
            }
            msg = WSMessage(
                event=MessageEventType.INIT_EVENT,
                data=data,
            )
            player: Player = self.get_player_from_seat(seat=seat)
            await self.game_manager.network_service.send_personal_message(
                message=msg.model_dump(),
                game_id=self.game_manager.game_id,
                user_id=player.uid,
            )

    def get_next_state(
        self,
        previous_event_type: GameEventType,
        next_event: GameEvent,
    ) -> RoundState:
        handlers: Mapping[
            GameEventType,
            Callable[[GameEventType, GameEvent], RoundState],
        ] = {
            GameEventType.HU: self._handle_hu,
            GameEventType.TSUMO: self._handle_tsumo,
            GameEventType.DISCARD: self._handle_discard,
            GameEventType.ROBBING_KONG: self._handle_robbing_kong,
            GameEventType.FLOWER: self._handle_action,
            GameEventType.AN_KAN: self._handle_action,
            GameEventType.DAIMIN_KAN: self._handle_action,
            GameEventType.CHII: self._handle_action,
            GameEventType.PON: self._handle_action,
            GameEventType.SHOMIN_KAN: self._handle_action,
            GameEventType.INIT_FLOWER: self._handle_init_flower,
        }

        try:
            handler = handlers[next_event.event_type]
        except KeyError:
            raise ValueError(f"Invalid next event type: {next_event.event_type}")

        return handler(previous_event_type, next_event)

    def _handle_hu(self, _: GameEventType, event: GameEvent) -> RoundState:
        return HuState(current_event=event)

    def _handle_tsumo(self, prev: GameEventType, _: GameEvent) -> RoundState:
        if self.tile_deck.tiles_remaining == 0:
            return DrawState()
        return TsumoState(prev_type=prev)

    def _handle_discard(self, prev: GameEventType, event: GameEvent) -> RoundState:
        tile = event.data.get("tile")
        if tile is None:
            raise ValueError("Discard tile must be provided for DISCARD turn.")
        return DiscardState(prev_type=prev, tile=tile)

    def _handle_robbing_kong(self, _: GameEventType, event: GameEvent) -> RoundState:
        tile = event.data.get("tile")
        if tile is None:
            raise ValueError("Robbing Kong tile must be provided.")
        return RobbingKongState(tile=tile)

    def _handle_action(self, _: GameEventType, event: GameEvent) -> RoundState:
        allowed = {
            GameEventType.FLOWER,
            GameEventType.AN_KAN,
            GameEventType.DAIMIN_KAN,
            GameEventType.SHOMIN_KAN,
            GameEventType.CHII,
            GameEventType.PON,
        }
        if event.event_type not in allowed:
            raise ValueError(
                f"_handle_action received invalid event type: {event.event_type}",
            )

        # Only the “replacement draw” events need to check for tiles_remaining
        if (
            event.event_type
            in {
                GameEventType.FLOWER,
                GameEventType.AN_KAN,
                GameEventType.DAIMIN_KAN,
                GameEventType.SHOMIN_KAN,
            }
            and self.tile_deck.tiles_remaining == 0
        ):
            raise ValueError("tiles not left to draw flower")

        return ActionState(current_event=event)

    def _handle_init_flower(self, _: GameEventType, __: GameEvent) -> RoundState:
        return FlowerState()

    async def do_robbing_kong(
        self,
        robbing_tile: GameTile,
    ) -> GameEvent | None:
        self.set_winning_conditions(
            winning_tile=robbing_tile,
            previous_event_type=GameEventType.SHOMIN_KAN,
        )
        actions_lists: list[list[Action]] = self.check_actions_after_shomin_kong()
        return await self.send_actions_and_wait(
            message_event_type=MessageEventType.ROBBING_KONG_ACTIONS,
            actions_lists=actions_lists,
        )

    def check_actions_after_shomin_kong(self) -> list[list[Action]]:
        result: list[list[Action]] = [[] for _ in range(self.game_manager.MAX_PLAYERS)]
        for player_seat in AbsoluteSeat:
            if player_seat == self.current_player_seat:
                continue
            logger.debug(
                f"[check_actions_after_shomin_kong] {player_seat} "
                f"hand cnt: {self.hands[player_seat].hand_size},"
                f"\n{self.hands[player_seat]}",
            )
            result[player_seat].extend(
                self.get_possible_hu_choices(player_seat=player_seat),
            )
        return result

    async def do_discard(
        self,
        previous_turn_type: GameEventType,
        discarded_tile: GameTile,
    ) -> GameEvent | None:
        self.hands[self.current_player_seat].apply_discard(discarded_tile)
        self.kawas[self.current_player_seat].append(discarded_tile)
        self.visible_tiles_count[discarded_tile] += 1
        self.set_winning_conditions(
            winning_tile=discarded_tile,
            previous_event_type=previous_turn_type,
        )

        actions_lists: list[list[Action]] = self.check_actions_after_discard()
        return await self.send_actions_and_wait(
            message_event_type=MessageEventType.DISCARD_ACTIONS,
            actions_lists=actions_lists,
        )

    def check_actions_after_discard(self) -> list[list[Action]]:
        result: list[list[Action]] = [[] for _ in range(self.game_manager.MAX_PLAYERS)]
        for player_seat in AbsoluteSeat:
            if player_seat == self.current_player_seat:
                continue
            result[player_seat].extend(
                self.get_possible_hu_choices(player_seat=player_seat),
            )
            result[player_seat].extend(
                self.get_possible_kan_choices(player_seat=player_seat),
            )
            result[player_seat].extend(
                self.get_possible_pon_choices(player_seat=player_seat),
            )
            result[player_seat].extend(
                self.get_possible_chii_choices(player_seat=player_seat),
            )
        return result

    async def send_actions_and_wait(
        self,
        message_event_type: MessageEventType,
        actions_lists: list[list[Action]],
    ) -> GameEvent | None:
        self.game_manager.increase_action_id()
        self.action_choices = [
            deepcopy(action) for action_list in actions_lists for action in action_list
        ]
        self.action_choices_list = deepcopy(actions_lists)

        pending_players, remaining_time = await self._initialize_pending_players(
            actions_lists=actions_lists,
            message_event_type=message_event_type,
        )

        self.action_manager = ActionManager(
            [action for action_list in actions_lists for action in action_list],
        )

        final_action, selected_events = await self._wait_for_player_actions(
            pending_players=pending_players,
            remaining_time=remaining_time,
        )
        self.action_choices.clear()
        self.action_choices_list.clear()
        self.game_manager.increase_action_id()
        self.action_manager = None
        if final_action is not None:
            response_event = self.pick_action_from_game_event_list(
                final_action,
                selected_events,
            )
            return response_event
        return None

    def get_player_from_seat(self, seat: AbsoluteSeat) -> Player:
        return self.game_manager.player_list[self.seat_to_player_index[seat]]

    async def _send_actions_message(
        self,
        seat: AbsoluteSeat,
        actions: list[Action],
        message_event_type: MessageEventType,
        left_time: float,
    ) -> None:
        msg = WSMessage(
            event=message_event_type,
            data={
                "tile": self.winning_conditions.winning_tile,
                "actions": actions,
                "action_id": self.game_manager.action_id,
                "left_time": left_time,
            },
        )
        if message_event_type == MessageEventType.TSUMO_ACTIONS:
            tenpai_assistant: TenpaiAssistant = TenpaiAssistant(
                game_hand=self.hands[seat],
                game_winning_conditions=self.winning_conditions,
                visible_tiles_count=self.visible_tiles_count,
                round_wind=AbsoluteSeat(self.game_manager.current_round // 4),
                seat_wind=seat,
            )
            msg.data["tenpai_assist"] = (
                tenpai_assistant.get_tenpai_assistance_info_in_full_hand()
            )
        player: Player = self.get_player_from_seat(seat=seat)
        await self.game_manager.network_service.send_personal_message(
            message=msg.model_dump(),
            game_id=self.game_manager.game_id,
            user_id=player.uid,
        )

    async def _initialize_pending_players(
        self,
        actions_lists: list[list[Action]],
        message_event_type: MessageEventType,
    ) -> tuple[set[AbsoluteSeat], dict[AbsoluteSeat, float]]:
        pending_players: set[AbsoluteSeat] = set()
        remaining_time: dict[AbsoluteSeat, float] = {}
        for seat in AbsoluteSeat:
            if actions_lists[seat]:
                pending_players.add(seat)
                remaining_time[seat] = self.DEFAULT_TURN_TIMEOUT
                await self._send_actions_message(
                    seat=seat,
                    actions=actions_lists[seat],
                    message_event_type=message_event_type,
                    left_time=remaining_time[seat],
                )
        return pending_players, remaining_time

    async def _wait_for_player_actions(
        self,
        pending_players: set[AbsoluteSeat],
        remaining_time: dict[AbsoluteSeat, float],
    ) -> tuple[Action | None, list[GameEvent]]:
        final_action: Action | None = None
        selected_events: list[GameEvent] = []
        if self.action_manager is None:
            raise ValueError("action manager is none")

        logger.debug(
            f"[DEBUG] Starting _wait_for_player_actions."
            f" Initial pending_players: {pending_players}",
        )
        while pending_players:
            wait_time = min(remaining_time[seat] for seat in pending_players)
            logger.debug(
                f"[DEBUG] Waiting for player action. Pending players:"
                f" {pending_players}, wait_time: {wait_time:.3f} seconds",
            )

            response_event, elapsed_time = await self.safe_wait_for(
                self.game_manager.event_queue.get(),
                wait_time,
            )
            logger.debug(
                f"[DEBUG] safe_wait_for returned event: {response_event}"
                f" (elapsed_time: {elapsed_time:.3f} seconds)",
            )

            if response_event is not None:
                self.game_manager.event_queue.task_done()
                pending_players.remove(response_event.player_seat)
                logger.debug(
                    f"[DEBUG] Received event from player "
                    f"{response_event.player_seat}: {response_event}",
                )
            else:
                logger.debug("[DEBUG] No event received within wait_time.")

            epsilon: float = 1e-9
            for seat in list(pending_players):
                remaining_time[seat] -= elapsed_time
                logger.debug(
                    f"[DEBUG] Updated remaining_time for seat {seat}:"
                    f" {remaining_time[seat]:.3f} seconds",
                )
                if remaining_time[seat] <= epsilon:
                    pending_players.remove(seat)
                    logger.debug(f"[DEBUG] Removed seat {seat} due to timeout.")

                    action = Action(
                        type=ActionType.SKIP,
                        seat_priority=RelativeSeat.create_from_absolute_seats(
                            current_seat=self.current_player_seat,
                            target_seat=seat,
                        ),
                        tile=GameTile.M1,
                    )
                    final_action = self.action_manager.push_action(action=action)
                    if final_action is not None:
                        logger.debug(
                            "[DEBUG] Final action selected, breaking out of wait loop.",
                        )
                        break
            if final_action is not None:
                break
            if response_event is not None:
                action = Action.create_from_game_event(
                    game_event=response_event,
                    current_player_seat=self.current_player_seat,
                )
                logger.debug(f"[DEBUG] Created action from received event: {action}")
                selected_events.append(deepcopy(response_event))
                final_action = self.action_manager.push_action(action)
                logger.debug(
                    f"[DEBUG] After push_action, final_action: {final_action},"
                    f" selected_events count: {len(selected_events)}",
                )
                if final_action is not None:
                    logger.debug(
                        "[DEBUG] Final action selected, breaking out of wait loop.",
                    )
                    break

        logger.debug(
            f"[DEBUG] Exiting _wait_for_player_actions. Final action: "
            f"{final_action}, total selected events: {len(selected_events)}",
        )
        return final_action, selected_events

    def pick_action_from_game_event_list(
        self,
        action: Action,
        game_events: list[GameEvent],
    ) -> GameEvent | None:
        for event in game_events:
            if (
                action.type == ActionType.create_from_game_event_type(event.event_type)
                and action.seat_priority
                == RelativeSeat.create_from_absolute_seats(
                    current_seat=self.current_player_seat,
                    target_seat=event.player_seat,
                )
                and action.tile == event.data.get("tile", None)
            ):
                return event
        return None

    async def end_round_as_hu(self, current_event: GameEvent) -> None:
        score_result: ScoreResult = self.get_score_result(hu_event=current_event)
        self.apply_score_result(
            hu_player_seat=current_event.player_seat,
            score_result=score_result,
        )
        await self.send_hu_hand_info(
            hu_player_seat=current_event.player_seat,
            score_result=score_result,
        )

    def apply_score_result(
        self,
        hu_player_seat: AbsoluteSeat,
        score_result: ScoreResult,
    ) -> None:
        total_score: int = (
            score_result.total_score + self.hands[hu_player_seat].flower_point
        )
        if hu_player_seat == self.current_player_seat:
            for player in self.game_manager.player_list:
                if player.index == self.seat_to_player_index[hu_player_seat]:
                    player.score += (total_score + 8) * 3
                else:
                    player.score -= total_score + 8
        else:
            for player in self.game_manager.player_list:
                if player.index == self.seat_to_player_index[hu_player_seat]:
                    player.score += total_score + 8 * 3
                elif (
                    player.index == self.seat_to_player_index[self.current_player_seat]
                ):
                    player.score -= total_score + 8
                else:
                    player.score -= 8

    def get_score_result(self, hu_event: GameEvent) -> ScoreResult:
        hand: Hand = Hand.create_from_game_hand(self.hands[hu_event.player_seat])
        if (
            self.winning_conditions.is_discarded
            or self.winning_conditions.is_robbing_the_kong
        ):
            if self.winning_conditions.winning_tile is None:
                raise ValueError("winning tile is None in Hu result page.")
            hand.tiles[
                Tile.create_from_game_tile(
                    GameTile(self.winning_conditions.winning_tile),
                )
            ] += 1
        return ScoreCalculator(
            hand=hand,
            winning_conditions=WinningConditions.create_from_game_winning_conditions(
                game_winning_conditions=self.winning_conditions,
                seat_wind=hu_event.player_seat,
                round_wind=AbsoluteSeat(self.game_manager.current_round // 4),
            ),
        ).result

    async def send_hu_hand_info(
        self,
        hu_player_seat: AbsoluteSeat,
        score_result: ScoreResult,
    ) -> None:
        an_kan_infos = [
            [
                block.first_tile
                for block in hand.call_blocks
                if block.type == CallBlockType.AN_KONG
            ]
            for hand in self.hands
        ]
        hu_hand: list[GameTile] = list(self.hands[hu_player_seat].tiles.elements())
        if (
            self.winning_conditions.is_discarded
            or self.winning_conditions.is_robbing_the_kong
        ) and self.winning_conditions.winning_tile is not None:
            hu_hand.append(self.winning_conditions.winning_tile)
        msg = WSMessage(
            event=MessageEventType.HU_HAND,
            data={
                "hand": hu_hand,
                "call_blocks": self.hands[hu_player_seat].call_blocks,
                "score_result": score_result,
                "player_seat": hu_player_seat,
                "current_player_seat": self.current_player_seat,
                "flower_count": self.hands[hu_player_seat].flower_point,
                "tsumo_tile": self.hands[hu_player_seat].tsumo_tile,
                "winning_tile": self.winning_conditions.winning_tile,
                "an_kan_infos": an_kan_infos,
            },
        )
        await self.game_manager.network_service.broadcast(
            message=msg.model_dump(),
            game_id=self.game_manager.game_id,
        )

    async def end_round_as_draw(self) -> None:
        await self.send_draw_info()

    async def send_draw_info(self) -> None:
        an_kan_infos = [
            [
                block.first_tile
                for block in hand.call_blocks
                if block.type == CallBlockType.AN_KONG
            ]
            for hand in self.hands
        ]
        msg = WSMessage(
            event=MessageEventType.DRAW,
            data={"an_kan_infos": an_kan_infos},
        )
        await self.game_manager.network_service.broadcast(
            message=msg.model_dump(),
            game_id=self.game_manager.game_id,
        )

    async def send_an_kan_info(self) -> None:
        an_kan_infos = [
            [
                block.first_tile
                for block in hand.call_blocks
                if block.type == CallBlockType.AN_KONG
            ]
            for hand in self.hands
        ]
        msg = WSMessage(
            event=MessageEventType.OPEN_AN_KAN,
            data={"an_kan_infos": an_kan_infos},
        )
        await self.game_manager.network_service.broadcast(
            message=msg.model_dump(),
            game_id=self.game_manager.game_id,
        )

    def check_actions_after_tsumo(self) -> list[list[Action]]:
        result: list[list[Action]] = [[] for _ in range(self.game_manager.MAX_PLAYERS)]
        result[self.current_player_seat].extend(
            self.get_possible_hu_choices(player_seat=self.current_player_seat),
        )
        result[self.current_player_seat].extend(
            self.get_possible_kan_choices(player_seat=self.current_player_seat),
        )
        result[self.current_player_seat].extend(
            self.get_possible_flower_choices(player_seat=self.current_player_seat),
        )
        return result

    def get_possible_hu_choices(self, player_seat: AbsoluteSeat) -> list[Action]:
        _hand: Hand = Hand.create_from_game_hand(hand=self.hands[player_seat])
        if self.winning_conditions.winning_tile is None:
            raise ValueError("[RoundManager.get_possible_hu_choices]tile is none")
        if GameTile(self.winning_conditions.winning_tile).is_flower:
            return []
        if (
            self.winning_conditions.is_discarded
            or self.winning_conditions.is_robbing_the_kong
        ):
            _hand.tiles[self.winning_conditions.winning_tile] += 1
        return (
            [
                Action(
                    type=ActionType.HU,
                    seat_priority=RelativeSeat.create_from_absolute_seats(
                        current_seat=self.current_player_seat,
                        target_seat=player_seat,
                    ),
                    tile=self.winning_conditions.winning_tile,
                ),
            ]
            if ScoreCalculator(
                hand=_hand,
                winning_conditions=WinningConditions.create_from_game_winning_conditions(
                    game_winning_conditions=self.winning_conditions,
                    seat_wind=player_seat,
                    round_wind=AbsoluteSeat(self.game_manager.current_round // 4),
                ),
            ).result.total_score
            >= self.game_manager.MINIMUM_HU_SCORE
            else []
        )

    def get_possible_flower_choices(self, player_seat: AbsoluteSeat) -> list[Action]:
        result: list[Action] = []
        if (
            self.winning_conditions.is_discarded
            or self.winning_conditions.is_last_tile_in_the_game
            or player_seat != self.current_player_seat
        ):
            return result
        for flower_tile in reversed(
            self.hands[player_seat].tiles
            & Counter(map(GameTile, GameTile.flower_tiles())),
        ):
            result.append(
                Action(
                    type=ActionType.FLOWER,
                    seat_priority=RelativeSeat.create_from_absolute_seats(
                        current_seat=self.current_player_seat,
                        target_seat=player_seat,
                    ),
                    tile=flower_tile,
                ),
            )
            break
        return result

    def get_possible_chii_choices(self, player_seat: AbsoluteSeat) -> list[Action]:
        result: list[Action] = []
        relative_seat: RelativeSeat = RelativeSeat.create_from_absolute_seats(
            current_seat=self.current_player_seat,
            target_seat=player_seat,
        )
        if (
            not self.winning_conditions.is_discarded
            or self.winning_conditions.is_last_tile_in_the_game
            or relative_seat != RelativeSeat.SHIMO
        ):
            return result
        result.extend(
            self.hands[player_seat].get_possible_chii_actions(
                priority=relative_seat,
                winning_condition=self.winning_conditions,
            ),
        )
        return result

    def get_possible_pon_choices(self, player_seat: AbsoluteSeat) -> list[Action]:
        result: list[Action] = []
        relative_seat: RelativeSeat = RelativeSeat.create_from_absolute_seats(
            current_seat=self.current_player_seat,
            target_seat=player_seat,
        )
        if (
            not self.winning_conditions.is_discarded
            or self.winning_conditions.is_last_tile_in_the_game
            or relative_seat == RelativeSeat.SELF
        ):
            return result
        result.extend(
            self.hands[player_seat].get_possible_pon_actions(
                priority=relative_seat,
                winning_condition=self.winning_conditions,
            ),
        )
        return result

    def get_possible_kan_choices(self, player_seat: AbsoluteSeat) -> list[Action]:
        result: list[Action] = []
        relative_seat: RelativeSeat = RelativeSeat.create_from_absolute_seats(
            current_seat=self.current_player_seat,
            target_seat=player_seat,
        )
        if self.winning_conditions.is_last_tile_in_the_game:
            return result
        result.extend(
            self.hands[player_seat].get_possible_kan_actions(
                priority=relative_seat,
                winning_condition=self.winning_conditions,
            ),
        )
        return result

    DEFAULT_TURN_TIMEOUT: Final[float] = 20

    async def wait_for_init_flower_ok(self) -> None:
        """
        모든 플레이어(예: self.game_manager.MAX_PLAYERS명)로부터"
        " INIT_FLOWER_OK 메시지를 기다립니다.
        첫 OK 메시지가 도착하면 10초 타임아웃을 적용하고, 10초 이내에"
        " 모든 OK가 도착하지 않으면 즉시 다음 상태로 진행합니다.
        """
        required_ok = self.game_manager.MAX_PLAYERS
        ok_received: set[AbsoluteSeat] = set()
        timeout: float | None = None
        logger.debug("[RoundManager] INIT_FLOWER_OK 응답을 기다립니다.")

        while len(ok_received) < required_ok:
            wait_time = timeout if timeout is not None else 9999.0
            try:
                event, elapsed = await self.safe_wait_for(
                    self.game_manager.event_queue.get(),
                    wait_time,
                )
            except TimeoutError:
                logger.debug("[RoundManager] 타임아웃 발생: 즉시 다음 상태로 전환")
                break
            if event is None:
                logger.debug("[RoundManager] 이벤트 수신 실패: 타임아웃")
                break
            self.game_manager.event_queue.task_done()
            elapsed

            if event.event_type == GameEventType.INIT_FLOWER_OK:
                ok_received.add(event.player_seat)
                logger.debug(
                    f"[RoundManager] OK 응답: {event.player_seat} "
                    f"(총 {len(ok_received)}/{required_ok})",
                )
                if timeout is None:
                    timeout = 60.0
            else:
                continue

        if len(ok_received) < required_ok:
            logger.debug(
                f"[RoundManager] 경고: {required_ok}명 중 "
                f"{len(ok_received)}명의 OK 응답만 수신: 즉시 TSUMO 상태로 전환",
            )
        else:
            logger.debug("[RoundManager] 모든 플레이어의 OK 응답 수신 완료.")

    async def _ticker(self) -> None:
        loop = asyncio.get_running_loop()
        last = loop.time()
        while True:
            now = loop.time()
            delta = now - last
            last = now

            self.remaining_time = max(0.0, self.remaining_time - delta)

            await asyncio.sleep(0.1)

    async def safe_wait_for(
        self,
        coroutine: Any,
        timeout: float | None = None,
    ) -> tuple[Any | None, float]:
        if timeout is not None:
            self.remaining_time = timeout

        loop = asyncio.get_running_loop()
        start = loop.time()
        logger.debug(
            f"[safe_wait_for] 시작: remaining_time={self.remaining_time:.3f}초",
        )

        ticker_task = asyncio.create_task(self._ticker())

        try:
            result = await asyncio.wait_for(coroutine, timeout=self.remaining_time)
            logger.debug(f"[safe_wait_for] 결과 받음: {result}")
        except TimeoutError:
            logger.debug("[safe_wait_for] 타임아웃 발생")
            result = None
        finally:
            ticker_task.cancel()
            with suppress(asyncio.CancelledError):
                await ticker_task

        elapsed = loop.time() - start

        self.remaining_time = max(0.0, self.remaining_time - elapsed)
        logger.debug(
            f"[safe_wait_for] 전체 소요: {elapsed:.3f}초, "
            "최종 남은 시간: {self.remaining_time:.3f}초",
        )

        return result, elapsed

    async def send_tsumo_actions_and_wait(
        self,
        actions_lists: list[list[Action]],
    ) -> GameEvent:
        logger.debug("[send_tsumo_actions_and_wait] 시작")
        self.game_manager.increase_action_id()
        self.action_choices = [
            deepcopy(action) for action_list in actions_lists for action in action_list
        ]
        self.action_choices_list = deepcopy(actions_lists)
        logger.debug(
            "[send_tsumo_actions_and_wait] action_id 증가: "
            f"{self.game_manager.action_id}",
        )
        await self._send_actions_message(
            message_event_type=MessageEventType.TSUMO_ACTIONS,
            actions=actions_lists[self.current_player_seat],
            left_time=self.DEFAULT_TURN_TIMEOUT,
            seat=self.current_player_seat,
        )
        await self.game_manager.network_service.broadcast(
            message=WSMessage(
                event=MessageEventType.TSUMO,
                data={
                    "seat": self.current_player_seat,
                },
            ).model_dump(),
            game_id=self.game_manager.game_id,
            exclude_user_id=self.game_manager.player_list[
                self.seat_to_player_index[self.current_player_seat]
            ].uid,
        )
        logger.debug("[send_tsumo_actions_and_wait] tsumo actions 메시지 전송 완료")

        response_event: GameEvent | None
        elapsed_time: float
        response_event, elapsed_time = await self.safe_wait_for(
            self.game_manager.event_queue.get(),
            self.DEFAULT_TURN_TIMEOUT,
        )
        logger.debug(
            f"[send_tsumo_actions_and_wait] event_queue 응답: {response_event}"
            f" (elapsed_time: {elapsed_time:.3f}초)",
        )
        self.action_choices.clear()
        self.action_choices_list.clear()
        self.game_manager.increase_action_id()
        if response_event is not None:
            self.game_manager.event_queue.task_done()
        if response_event is None:
            logger.debug(
                "[send_tsumo_actions_and_wait] 응답 없음 - 자동 DISCARD 이벤트 생성",
            )
            self.game_manager.increase_action_id()

            rightmost_tile: GameTile | None = self.hands[
                self.current_player_seat
            ].get_rightmost_tile()
            if not rightmost_tile:
                raise ValueError("no tile in hand")
            response_event = GameEvent(
                event_type=GameEventType.DISCARD,
                player_seat=self.current_player_seat,
                action_id=self.game_manager.action_id,
                data={"tile": rightmost_tile},
            )
            msg = WSMessage(
                event=MessageEventType.DISCARD,
                data={
                    "tile": rightmost_tile,
                    "seat": self.current_player_seat,
                    "is_tsumogiri": True,
                },
            )
            await self.game_manager.network_service.broadcast(
                message=msg.model_dump(),
                game_id=self.game_manager.game_id,
            )
            logger.debug(
                "[send_tsumo_actions_and_wait] "
                f"생성된 자동 DISCARD 이벤트: {response_event}",
            )
        else:
            logger.debug("[send_tsumo_actions_and_wait] 정상 응답 이벤트 수신")

        logger.debug(
            "[send_tsumo_actions_and_wait] "
            f"최종 action_id: {self.game_manager.action_id}",
        )
        return response_event

    async def wait_discard_after_call_action(
        self,
    ) -> GameEvent:
        await self.game_manager.network_service.send_personal_message(
            message=WSMessage(
                event=MessageEventType.SET_TIMER,
                data={
                    "remaining_time": self.DEFAULT_TURN_TIMEOUT,
                },
            ).model_dump(),
            game_id=self.game_manager.game_id,
            user_id=self.game_manager.player_list[
                self.seat_to_player_index[self.current_player_seat]
            ].uid,
        )
        response_event: GameEvent | None
        elapsed_time: float
        response_event, elapsed_time = await self.safe_wait_for(
            self.game_manager.event_queue.get(),
            self.DEFAULT_TURN_TIMEOUT,
        )
        self.game_manager.increase_action_id()
        if response_event is not None:
            self.game_manager.event_queue.task_done()
        elapsed_time
        if response_event is None:
            rightmost_tile: GameTile | None = self.hands[
                self.current_player_seat
            ].get_rightmost_tile()
            if not rightmost_tile:
                raise ValueError("no tile in hand")
            response_event = GameEvent(
                event_type=GameEventType.DISCARD,
                player_seat=self.current_player_seat,
                action_id=self.game_manager.action_id,
                data={"tile": rightmost_tile},
            )
            msg = WSMessage(
                event=MessageEventType.DISCARD,
                data={
                    "tile": rightmost_tile,
                    "seat": self.current_player_seat,
                    "is_tsumogiri": False,
                },
            )
            await self.game_manager.network_service.broadcast(
                message=msg.model_dump(),
                game_id=self.game_manager.game_id,
            )
            logger.debug(
                "[wait_discard_after_call_action] "
                f"생성된 자동 DISCARD 이벤트: {response_event}",
            )
        self.game_manager.increase_action_id()
        return response_event

    async def do_action(self, current_event: GameEvent) -> RoundState:
        source_player_seat: AbsoluteSeat = self.current_player_seat
        self.current_player_seat = current_event.player_seat
        applied_result = self.apply_response_event(
            response_event=current_event,
            source_player_seat=source_player_seat,
        )
        await self.send_response_event(
            response_event=current_event,
            applied_result=applied_result,
        )
        match current_event.event_type:
            case GameEventType.SHOMIN_KAN:
                tile: GameTile | None = current_event.data.get("tile", None)
                if tile is None:
                    raise ValueError("tile is None")
                return RobbingKongState(tile=tile)
            case GameEventType.DAIMIN_KAN | GameEventType.AN_KAN:
                if self.tile_deck.tiles_remaining == 0:
                    return DrawState()
                return TsumoState(prev_type=current_event.event_type)
            case GameEventType.CHII | GameEventType.PON:
                discard_event: GameEvent = await self.wait_discard_after_call_action()
                discard_tile: GameTile = discard_event.data.get("tile", None)
                if discard_tile is None:
                    raise ValueError("Tile is None")
                return DiscardState(
                    prev_type=current_event.event_type,
                    tile=discard_tile,
                )
            case GameEventType.FLOWER:
                if self.tile_deck.tiles_remaining == 0:
                    return DrawState()
                return TsumoState(
                    prev_type=current_event.event_type,
                )
            case _:
                raise ValueError("invalid action")

    def apply_response_event(
        self,
        response_event: GameEvent,
        source_player_seat: AbsoluteSeat,
    ) -> Any:
        match response_event.event_type:
            case GameEventType.FLOWER:
                if self.tile_deck.tiles_remaining < 1:
                    raise IndexError("Tile not left in deck in flower applying")
                flower_tile = self.hands[response_event.player_seat].apply_flower()
                if flower_tile is None:
                    raise ValueError("No flower tile while applying flower")
                return flower_tile
            case (
                GameEventType.SHOMIN_KAN
                | GameEventType.DAIMIN_KAN
                | GameEventType.AN_KAN
                | GameEventType.CHII
                | GameEventType.PON
            ):
                if self.winning_conditions.winning_tile is None:
                    raise ValueError("discarded tile is None")
                tile: GameTile | None = response_event.data.get("tile", None)
                if tile is None:
                    raise ValueError("No tile data in call block")
                call_block: CallBlock = CallBlock.create_from_game_event(
                    game_event=response_event,
                    current_seat=source_player_seat,
                    source_tile=self.winning_conditions.winning_tile,
                )
                self.hands[response_event.player_seat].apply_call(block=call_block)
                if response_event.event_type in {
                    GameEventType.CHII,
                    GameEventType.PON,
                    GameEventType.DAIMIN_KAN,
                }:
                    if len(self.kawas[source_player_seat]) == 0:
                        raise IndexError("kawa is empty.")
                    self.kawas[source_player_seat].pop()
                self.apply_call_to_visible_tiles(call_block=call_block)
                return call_block

    def apply_call_to_visible_tiles(self, call_block: CallBlock) -> None:
        match call_block.type:
            case CallBlockType.CHII:
                for index in range(3):
                    if index == call_block.source_tile_index:
                        continue
                    self.visible_tiles_count[
                        GameTile(call_block.first_tile + index)
                    ] += 1
            case CallBlockType.PUNG:
                self.visible_tiles_count[call_block.first_tile] += 2
            case CallBlockType.DAIMIN_KONG:
                self.visible_tiles_count[call_block.first_tile] += 3
            case CallBlockType.SHOMIN_KONG:
                self.visible_tiles_count[call_block.first_tile] += 1

    async def send_response_event(
        self,
        response_event: GameEvent,
        applied_result: Any,
    ) -> None:
        self.game_manager.increase_action_id()
        if response_event.event_type in {GameEventType.CHII, GameEventType.PON}:
            tenpai_assistant: TenpaiAssistant = TenpaiAssistant(
                game_hand=self.hands[response_event.player_seat],
                game_winning_conditions=self.winning_conditions,
                visible_tiles_count=self.visible_tiles_count,
                round_wind=AbsoluteSeat(self.game_manager.current_round // 4),
                seat_wind=response_event.player_seat,
            )
            tenpai_assist_data = (
                tenpai_assistant.get_tenpai_assistance_info_in_full_hand()
            )
        match response_event.event_type:
            case GameEventType.FLOWER:
                msg = WSMessage(
                    event=MessageEventType.FLOWER,
                    data={
                        "seat": response_event.player_seat,
                        "tile": response_event.data["tile"],
                        "source_seat": self.current_player_seat,
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                )
            case GameEventType.AN_KAN:
                msg_personal = WSMessage(
                    event=MessageEventType.AN_KAN,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                        "has_tsumo_tile": self.winning_conditions.winning_tile
                        == applied_result.first_tile,
                    },
                )
                await self.game_manager.network_service.send_personal_message(
                    message=msg_personal.model_dump(),
                    game_id=self.game_manager.game_id,
                    user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_event.player_seat]
                    ].uid,
                )
                msg_broadcast = WSMessage(
                    event=MessageEventType.AN_KAN,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": CallBlock(
                            type=CallBlockType.AN_KONG,
                            first_tile=GameTile.F0,
                            source_seat=RelativeSeat.SELF,
                        ),
                        "has_tsumo_tile": self.winning_conditions.winning_tile
                        == applied_result.first_tile,
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg_broadcast.model_dump(),
                    game_id=self.game_manager.game_id,
                    exclude_user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_event.player_seat]
                    ].uid,
                )
            case GameEventType.CHII:
                msg_personal = WSMessage(
                    event=MessageEventType.CHII,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                        "action_id": self.game_manager.action_id,
                        "tenpai_assist": tenpai_assist_data,
                    },
                )
                await self.game_manager.network_service.send_personal_message(
                    message=msg_personal.model_dump(),
                    game_id=self.game_manager.game_id,
                    user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_event.player_seat]
                    ].uid,
                )
                msg = WSMessage(
                    event=MessageEventType.CHII,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                    exclude_user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_event.player_seat]
                    ].uid,
                )
            case GameEventType.PON:
                msg_personal = WSMessage(
                    event=MessageEventType.PON,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                        "action_id": self.game_manager.action_id,
                        "tenpai_assist": tenpai_assist_data,
                    },
                )
                await self.game_manager.network_service.send_personal_message(
                    message=msg_personal.model_dump(),
                    game_id=self.game_manager.game_id,
                    user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_event.player_seat]
                    ].uid,
                )
                msg = WSMessage(
                    event=MessageEventType.PON,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                    exclude_user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_event.player_seat]
                    ].uid,
                )
            case GameEventType.DAIMIN_KAN:
                msg = WSMessage(
                    event=MessageEventType.DAIMIN_KAN,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                )
            case GameEventType.SHOMIN_KAN:
                msg = WSMessage(
                    event=MessageEventType.SHOMIN_KAN,
                    data={
                        "seat": response_event.player_seat,
                        "call_block_data": applied_result,
                        "has_tsumo_tile": self.winning_conditions.winning_tile
                        == applied_result.first_tile,
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                )
            case GameEventType.DISCARD:
                msg = WSMessage(
                    event=MessageEventType.DISCARD,
                    data={
                        "tile": response_event.data["tile"],
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                )

    def set_winning_conditions(
        self,
        winning_tile: GameTile,
        previous_event_type: GameEventType,
    ) -> None:
        self.winning_conditions.winning_tile = winning_tile
        self.winning_conditions.is_discarded = previous_event_type.is_next_discard
        self.winning_conditions.is_last_tile_of_its_kind = (
            self.visible_tiles_count.get(winning_tile, 0) == 4
            and self.winning_conditions.is_discarded
        ) or (
            self.visible_tiles_count.get(winning_tile, 0) == 3
            and not self.winning_conditions.is_discarded
        )
        self.winning_conditions.is_last_tile_in_the_game = (
            self.tile_deck.tiles_remaining == 0
        )
        self.winning_conditions.is_replacement_tile = previous_event_type.is_kong
        self.winning_conditions.is_robbing_the_kong = (
            previous_event_type == GameEventType.SHOMIN_KAN
        )

    async def do_tsumo(self, previous_event_type: GameEventType) -> GameEvent:
        drawn_tile: GameTile | None
        if self.tile_deck.HAIPAI_TILES < 1:
            raise ValueError(
                f"Not enough tiles remaining. Requested: {1},"
                f" Available: {self.tile_deck.HAIPAI_TILES}",
            )

        if previous_event_type == GameEventType.DISCARD:
            self.current_player_seat = self.current_player_seat.next_seat
        if previous_event_type != GameEventType.INIT_FLOWER:
            drawn_tiles: list[GameTile]
            if previous_event_type.is_next_replacement:
                drawn_tiles = self.tile_deck.draw_tiles_right(1)
            else:
                drawn_tiles = self.tile_deck.draw_tiles(1)
            if len(drawn_tiles) < 1:
                raise IndexError("cannot tsumo when tile's not left in deck")
            drawn_tile = drawn_tiles[0]
            self.hands[self.current_player_seat].apply_tsumo(tile=drawn_tile)
        else:
            drawn_tile = self.hands[self.current_player_seat].tsumo_tile
            if drawn_tile is None:
                raise ValueError("init player did not tsumo.")
        self.set_winning_conditions(
            winning_tile=drawn_tile,
            previous_event_type=previous_event_type,
        )

        actions_lists: list[list[Action]] = self.check_actions_after_tsumo()
        return await self.send_tsumo_actions_and_wait(
            actions_lists=actions_lists,
        )

    async def wait_for_next_round_confirm(self) -> None:
        """
        모든 플레이어(MAX_PLAYERS명)로부터 NEXT_ROUND_CONFIRM 메시지를 기다립니다.
        첫 Confirm 메시지가 도착하면 10초 타임아웃을 적용하고,
        10초 이내에 모든 Confirm 응답이 수신되지 않으면 즉시 다음 라운드로 진행합니다.
        만약 전체 플레이어로부터 60초 동안 아무런 메시지도 수신하지 않으면,
        즉시 다음 라운드로 진행합니다.
        """
        required_confirm = self.game_manager.MAX_PLAYERS
        confirm_received: set[AbsoluteSeat] = set()
        timeout: float | None = None
        start_time = time.time()
        logger.debug("[RoundManager] NEXT_ROUND_CONFIRM 응답을 기다립니다.")

        while len(confirm_received) < required_confirm:
            elapsed_since_start = time.time() - start_time
            if elapsed_since_start >= 60:
                logger.debug(
                    "[RoundManager] 전체 플레이어로부터 응답이 60초 동안"
                    " 없습니다. 즉시 다음 라운드 진행합니다.",
                )
                break

            wait_time = timeout if timeout is not None else 9999.0
            event: GameEvent | None
            elapsed: float
            try:
                event, elapsed = await self.safe_wait_for(
                    self.game_manager.event_queue.get(),
                    wait_time,
                )
                elapsed
            except TimeoutError:
                logger.debug("[RoundManager] 타임아웃 발생: 즉시 다음 상태로 전환")
                break
            if event is None:
                logger.debug("[RoundManager] 이벤트 수신 실패: 타임아웃")
                break
            self.game_manager.event_queue.task_done()

            if event.event_type == GameEventType.NEXT_ROUND_CONFIRM:
                confirm_received.add(event.player_seat)
                logger.debug(
                    f"[RoundManager] Confirm 응답: {event.player_seat} "
                    f"(총 {len(confirm_received)}/{required_confirm})",
                )
                if timeout is None:
                    timeout = 60.0
            else:
                continue

        if len(confirm_received) < required_confirm:
            logger.debug(
                f"[RoundManager] 경고: {required_confirm}명 중 "
                f"{len(confirm_received)}명의 Confirm 응답만 수신됨:"
                " 즉시 다음 라운드 진행",
            )
        else:
            logger.debug("[RoundManager] 모든 플레이어의 Confirm 응답 수신 완료.")


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

        for _ in range(self.TOTAL_ROUNDS):
            await self.round_manager.run_round()
            self.current_round = self.current_round.next_round
        await self.submit_game_result()

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
        endpoint = (
            f"https://{settings.COER_SERVER_URL}/internal/rooms/{self.game_id}/end-game"
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.post(endpoint)
                resp.raise_for_status()
                logger.debug("[GameManager] end-game 요청 성공: %s", resp.json())
            except httpx.HTTPError as exc:
                logger.debug("[GameManager] end-game 요청 실패: %s", exc)

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


class ActionManager:
    def __init__(self, action_list: list[Action]):
        self.action_heap: list[Action] = action_list
        heapq.heapify(self.action_heap)
        self.selected_action_heap: list[Action] = []
        self.finished_players: set[RelativeSeat] = set()
        self.final_action: Action | None = None

    def empty(self) -> bool:
        return not self.action_heap

    def push_action(self, action: Action) -> Action | None:
        """
        새로운 Action을 push하고, 최종 선택된 우선순위 높은 valid Action을 반환

        Args:
            action (Action): 추가할 Action

        Returns:
            Action | None: 최종 Action (없으면 None)
        """
        if self.final_action:
            return self.final_action
        if action.type != ActionType.SKIP:
            heapq.heappush(self.selected_action_heap, action)
        self.finished_players.add(action.seat_priority)
        while (
            self.action_heap
            and self.selected_action_heap
            and self.action_heap[0].seat_priority in self.finished_players
        ):
            top_action: Action = heapq.heappop(self.action_heap)
            if top_action == self.selected_action_heap[0]:
                self.final_action = top_action
                break
        return self.final_action
