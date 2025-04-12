from __future__ import annotations

import asyncio
import heapq
from collections import Counter
from collections.abc import Awaitable
from copy import deepcopy
from random import shuffle
from typing import Any, Final, TypeVar

from app.core.network_service import NetworkService
from app.schemas.ws import MessageEventType, WSMessage
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
from app.services.game_manager.models.round_fsm import (
    DiscardState,
    DrawState,
    FlowerState,
    HuState,
    InitState,
    RobbingKongState,
    RoundState,
    TsumoState,
)
from app.services.game_manager.models.types import (
    ActionType,
    CallBlockType,
    GameEventType,
)
from app.services.game_manager.models.winning_conditions import (
    GameWinningConditions,
)
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.result.result import ScoreResult
from app.services.score_calculator.score_calculator import ScoreCalculator
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)


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

    async def run_round(self) -> None:
        state: RoundState | None = InitState()
        while state is not None:
            state = await state.run(self)

    def init_round_data(self) -> None:
        self.tile_deck = Deck()
        self.hands = [
            GameHand.create_from_tiles(tiles=self.tile_deck.draw_haipai())
            for _ in range(self.game_manager.MAX_PLAYERS)
        ]
        self.hands[AbsoluteSeat.EAST].apply_tsumo(
            tile=self.tile_deck.draw_tiles(count=1)[0],
        )
        self.kawas = [[] for _ in range(self.game_manager.MAX_PLAYERS)]
        self.visible_tiles_count = Counter()
        self.winning_conditions = GameWinningConditions.create_default_conditions()
        self.init_seat_index_mapping()
        self.action_manager = None
        self.current_player_seat = AbsoluteSeat.EAST

    def init_seat_index_mapping(self) -> None:
        shift = self.game_manager.current_round.number - 1
        wind = self.game_manager.current_round.wind
        base_mapping = {
            "E": {
                AbsoluteSeat.EAST: 0,
                AbsoluteSeat.SOUTH: 1,
                AbsoluteSeat.WEST: 2,
                AbsoluteSeat.NORTH: 3,
            },
            "S": {
                AbsoluteSeat.EAST: 1,
                AbsoluteSeat.SOUTH: 0,
                AbsoluteSeat.WEST: 3,
                AbsoluteSeat.NORTH: 2,
            },
            "W": {
                AbsoluteSeat.EAST: 2,
                AbsoluteSeat.SOUTH: 3,
                AbsoluteSeat.WEST: 1,
                AbsoluteSeat.NORTH: 0,
            },
            "N": {
                AbsoluteSeat.EAST: 3,
                AbsoluteSeat.SOUTH: 2,
                AbsoluteSeat.WEST: 0,
                AbsoluteSeat.NORTH: 1,
            },
        }[wind]
        self.seat_to_player_index = {
            seat: (base + shift) % 4 for seat, base in base_mapping.items()
        }
        self.player_index_to_seat = {v: k for k, v in self.seat_to_player_index.items()}

    async def send_init_events(self) -> None:
        for seat in AbsoluteSeat:
            player: Player = self.get_player_from_seat(seat=seat)
            msg = WSMessage(
                event=MessageEventType.INIT_EVENT,
                data={
                    "player_seat": seat,
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
        for seat in AbsoluteSeat:
            while self.hands[seat].has_flower:
                if (applied_flower := self.hands[seat].apply_flower()) is None:
                    raise ValueError("Invalid hand value about flower tiles")
                applied_flowers_list[seat].append(applied_flower)
                new_tile: GameTile = self.tile_deck.draw_tiles_right(1)[0]
                self.hands[seat].apply_init_flower_tsumo(tile=new_tile)
                new_tiles_list[seat].append(new_tile)
        flower_count: list[int] = [hand.flower_point for hand in self.hands]
        for seat in AbsoluteSeat:
            data: dict[str, Any] = {
                "new_tiles": new_tiles_list[seat],
                "applied_flowers": applied_flowers_list[seat],
                "flower_count": flower_count,
            }
            msg = WSMessage(
                event=MessageEventType.INIT_FLOWER_REPLACEMENT,
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
        tile: GameTile | None
        match next_event.event_type:
            case GameEventType.HU:
                return HuState(current_event=next_event)
            case GameEventType.TSUMO:
                if self.tile_deck.tiles_remaining == 0:
                    return DrawState()
                return TsumoState(prev_type=previous_event_type)
            case GameEventType.DISCARD:
                tile = next_event.data.get("tile", None)
                if tile is None:
                    raise ValueError("Discard tile must be provided for DISCARD turn.")
                return DiscardState(prev_type=previous_event_type, tile=tile)
            case GameEventType.ROBBING_KONG:
                tile = next_event.data.get("tile", None)
                if tile is None:
                    raise ValueError(
                        "ShominKong tile must be provided for ROBBING KONG turn.",
                    )
                return RobbingKongState(tile=tile)
            case GameEventType.INIT_FLOWER:
                return FlowerState()
            case _:
                raise ValueError(f"Invalid next event type: {next_event.event_type}")

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
        while pending_players:
            wait_time = min(remaining_time[seat] for seat in pending_players)
            response_event, elapsed_time = await self.safe_wait_for(
                self.game_manager.event_queue.get(),
                wait_time,
            )
            self.game_manager.event_queue.task_done()

            epsilon: float = 1e-9
            for seat in list(pending_players):
                remaining_time[seat] -= elapsed_time
                if remaining_time[seat] <= epsilon:
                    pending_players.remove(seat)

            if response_event is not None:
                selected_events.append(deepcopy(response_event))
                final_action = self.action_manager.push_action(
                    Action.create_from_game_event(
                        game_event=response_event,
                        current_player_seat=self.current_player_seat,
                    ),
                )
                if final_action is not None:
                    break
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
        await self.send_an_kan_info()

    def apply_score_result(
        self,
        hu_player_seat: AbsoluteSeat,
        score_result: ScoreResult,
    ) -> None:
        if hu_player_seat == self.current_player_seat:
            for player in self.game_manager.player_list:
                if player.index == self.seat_to_player_index[hu_player_seat]:
                    player.score += (score_result.total_score + 8) * 3
                else:
                    player.score -= score_result.total_score + 8
        else:
            for player in self.game_manager.player_list:
                if player.index == self.seat_to_player_index[hu_player_seat]:
                    player.score += score_result.total_score + 8 * 3
                elif (
                    player.index == self.seat_to_player_index[self.current_player_seat]
                ):
                    player.score -= score_result.total_score + 8
                else:
                    player.score -= 8

    def get_score_result(self, hu_event: GameEvent) -> ScoreResult:
        return ScoreCalculator(
            hand=Hand.create_from_game_hand(self.hands[hu_event.player_seat]),
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
        msg = WSMessage(
            event=MessageEventType.HU_HAND,
            data={
                "hand": list(self.hands[hu_player_seat].tiles.elements()),
                "score_result": score_result,
                "player_seat": hu_player_seat,
            },
        )
        await self.game_manager.network_service.broadcast(
            message=msg.model_dump(),
            game_id=self.game_manager.game_id,
        )

    async def end_round_as_draw(self) -> None:
        await self.send_an_kan_info()

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
            event=MessageEventType.FLOWER,
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
        if self.winning_conditions.winning_tile.is_flower:
            return []
        if self.winning_conditions.is_discarded:
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
        for flower_tile in self.hands[player_seat].tiles & Counter(
            map(GameTile, GameTile.flower_tiles()),
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

    T = TypeVar("T")
    DEFAULT_TURN_TIMEOUT: Final[float] = 60.0

    async def safe_wait_for(
        self,
        coroutine: Awaitable[T],
        timeout: float,
    ) -> tuple[T | None, float]:
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        start: float = loop.time()
        try:
            result = await asyncio.wait_for(coroutine, timeout=timeout)
        except TimeoutError:
            result = None
        elapsed = loop.time() - start
        return result, elapsed

    async def send_tsumo_actions_and_wait(
        self,
        actions_lists: list[list[Action]],
    ) -> GameEvent:
        self.game_manager.increase_action_id()
        await self._send_actions_message(
            message_event_type=MessageEventType.TSUMO_ACTIONS,
            actions=actions_lists[self.current_player_seat],
            left_time=self.DEFAULT_TURN_TIMEOUT,
            seat=self.current_player_seat,
        )
        response_event: GameEvent | None
        elapsed_time: float
        response_event, elapsed_time = await self.safe_wait_for(
            self.game_manager.event_queue.get(),
            self.DEFAULT_TURN_TIMEOUT,
        )
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
        self.game_manager.increase_action_id()
        return response_event

    async def wait_discard_after_call_action(
        self,
    ) -> GameEvent:
        self.game_manager.increase_action_id()
        response_event: GameEvent | None
        elapsed_time: float
        response_event, elapsed_time = await self.safe_wait_for(
            self.game_manager.event_queue.get(),
            self.DEFAULT_TURN_TIMEOUT,
        )
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
        self.game_manager.increase_action_id()
        return response_event

    async def do_action(self, current_event: GameEvent) -> RoundState:
        await self.send_response_event(response_event=current_event)
        self.apply_response_event(response_event=current_event)
        match current_event.event_type:
            case GameEventType.SHOMIN_KAN:
                tile: GameTile | None = current_event.data.get("tile", None)
                if tile is None:
                    raise ValueError("tile is None")
                return RobbingKongState(tile=tile)
            case GameEventType.DAIMIN_KAN | GameEventType.AN_KAN:
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
            case _:
                raise ValueError("invalid action")

    def apply_response_event(
        self,
        response_event: GameEvent,
    ) -> None:
        match response_event.event_type:
            case (
                GameEventType.SHOMIN_KAN
                | GameEventType.DAIMIN_KAN
                | GameEventType.AN_KAN
                | GameEventType.CHII
                | GameEventType.PON
            ):
                if self.winning_conditions.winning_tile is None:
                    raise ValueError("discarded tile is None")
                call_block: CallBlock = CallBlock.create_from_game_event(
                    game_event=response_event,
                    current_seat=self.current_player_seat,
                    source_tile=self.winning_conditions.winning_tile,
                )
                self.hands[response_event.player_seat].apply_call(block=call_block)
                if len(self.kawas[self.current_player_seat]) == 0:
                    raise IndexError("kawa is empty.")
                self.apply_call_to_visible_tiles(call_block=call_block)
                self.kawas[self.current_player_seat].pop()
                self.current_player_seat = response_event.player_seat

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
    ) -> None:
        match response_event.event_type:
            case GameEventType.FLOWER:
                msg = WSMessage(
                    event=MessageEventType.FLOWER,
                    data={
                        "player_seat": response_event.player_seat,
                        "tile": None,
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
                        "player_seat": response_event.player_seat,
                        "tile": response_event.data["tile"],
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
                        "player_seat": response_event.player_seat,
                        "tile": None,
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
                msg = WSMessage(
                    event=MessageEventType.CHII,
                    data={
                        "player_seat": response_event.player_seat,
                        "tile": response_event.data["tile"],
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                )
            case GameEventType.PON:
                msg = WSMessage(
                    event=MessageEventType.PON,
                    data={
                        "player_seat": response_event.player_seat,
                        "tile": response_event.data["tile"],
                    },
                )
                await self.game_manager.network_service.broadcast(
                    message=msg.model_dump(),
                    game_id=self.game_manager.game_id,
                )
            case GameEventType.DAIMIN_KAN:
                msg = WSMessage(
                    event=MessageEventType.DAIMIN_KAN,
                    data={
                        "player_seat": response_event.player_seat,
                        "tile": response_event.data["tile"],
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
                        "player_seat": response_event.player_seat,
                        "tile": response_event.data["tile"],
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
            self.visible_tiles_count.get(winning_tile, 0) == 3
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
                "Not enough tiles remaining. Requested: {1},"
                " Available: {self.tile_deck.HAIPAI_TILES}",
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
        # TODO: submit game result to core server
        pass

    def increase_action_id(self) -> None:
        self.action_id += 1


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
        heapq.heappush(self.selected_action_heap, action)
        self.finished_players.add(action.seat_priority)
        while (
            self.action_heap
            and self.action_heap[0].seat_priority in self.finished_players
        ):
            top_action: Action = heapq.heappop(self.action_heap)
            if top_action == self.selected_action_heap[0]:
                self.final_action = top_action
                break
        return self.final_action
