from __future__ import annotations

import asyncio
import heapq
from collections import Counter
from collections.abc import Awaitable
from copy import deepcopy
from random import shuffle
from typing import Any, Final, TypeVar

from fastapi import Depends

from app.core.network_service import NetworkService
from app.core.room_manager import RoomManager
from app.dependencies.network_service import get_network_service
from app.dependencies.room_manager import get_room_manager
from app.schemas.ws import MessageEventType
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
    InitState,
    RobbingKongState,
    RoundState,
    TsumoState,
)
from app.services.game_manager.models.types import ActionType, GameEventType
from app.services.game_manager.models.winning_conditions import (
    GameWinningConditions,
)
from app.services.score_calculator.hand.hand import Hand
from app.services.score_calculator.score_calculator import ScoreCalculator
from app.services.score_calculator.winning_conditions.winning_conditions import (
    WinningConditions,
)


class RoundManager:
    """
    Game의 한 국(Round)의 로직을 관리하는 Class

    Attributes:
        game_manager (GameManager): GameManager에 대한 참조 end_round에 대한
            정보를 주거나, action_id를 받아오기 위함
        tile_deck (Deck): 패산
        hand_list (list[GameHand]): 각 플레이어(절대 위치 자리(동가, 남가, 서가, 북가))
        의 손패 리스트
        kawa_list (list[list[GameTile]]): 각 플레이어의 강
        visible_tiles_count (Counter[GameTile]): 보이는 타일의 개수를 관리하는 카운터
            (화절장 조건을 알기 위해 존재)
        winning_conditions (GameWinningConditions): 화료 조건 flag들
        seat_to_player_index (dict[AbsoluteSeat, int]): 절대 좌표와 player index의 매핑
            (e.g. game_manager.players_list[seat_to_player_index[current_player_seat]])
        action_manager (ActionManager | None): Action 우선순위를 heap으로 관리하여 실행
            Action을 결정하는 manager
        current_player_seat (AbsoluteSeat): 현재 턴이 수행되고 있는 플레이어의 절대 위치
            자리
    """

    def __init__(self, game_manager: GameManager) -> None:
        """
        RoundManager 인스턴스를 초기화

        Args:
            game_manager (GameManager): 이 Round를 소유하는 GameManager
        """
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
            for _ in range(GameManager.MAX_PLAYERS)
        ]
        self.kawas = [[] for _ in range(GameManager.MAX_PLAYERS)]
        self.visible_tiles_count = Counter()
        self.winning_conditions = GameWinningConditions.create_default_conditions()
        self.action_manager = None
        self.current_player_seat = AbsoluteSeat.EAST

    async def send_init_events(self) -> None:
        for seat in AbsoluteSeat:
            init_data = {"hand": self.hands[seat].tiles.elements()}
            init_event = GameEvent(
                event_type=GameEventType.INIT_HAIPAI,
                player_seat=seat,
                data=init_data,
                action_id=self.game_manager.action_id,
            )
            await self.game_manager.event_queue.put(init_event)

    async def do_init_flower_action(self) -> None:
        for seat in AbsoluteSeat:
            data: dict[str, Any] = {
                "new_tiles": [],
            }
            while self.hands[seat].has_flower:
                self.hands[seat].apply_flower()
                new_tile: GameTile = self.tile_deck.draw_tiles_right(1)[0]
                self.hands[seat].apply_tsumo(tile=new_tile)
                data["new_tiles"].append(new_tile)
            self.game_manager.increase_action_id()
            event = GameEvent(
                event_type=GameEventType.INIT_FLOWER,
                player_seat=seat,
                data=data,
                action_id=self.game_manager.action_id,
            )
            await self.game_manager.event_queue.put(event)

    # TODO previous game event기반 state 추론으로 바꿔야함
    def get_next_state(
        self,
        previous_event_type: GameEventType,
        next_event: GameEvent,
    ) -> RoundState:
        tile: GameTile | None
        match next_event.event_type:
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
            case _:
                raise ValueError(f"Invalid next event type: {next_event.event_type}")

    async def proceed_next_turn(
        self,
        previous_turn_type: GameEventType,
        previous_action: Action | None = None,
        discarded_tile: GameTile | None = None,
    ) -> None:
        """
        이전 TurnType과 수행한 Action에 따라 다음 턴으로 진행함
        쯔모 해야하는데 패산에 남은 타일이 없는 경우 유국

        Args:
            previous_turn_type (TurnType): 이전 턴의 타입
            previous_action (Action | None): 이전 턴에서 수행한 액션 (없을 수도 있음
                (e.g. Discard의 경우 Action class에 속하지 않음))

        Raises:
            ValueError: 다음 턴 타입이 유효하지 않을 경우. (next_seat_after_action의
                현재 구조상 도달할 수 없으나 이후 해당함수의 변경에 대비해 설정)
        """
        self.move_current_player_seat_to_next(previous_action=previous_action)
        match previous_turn_type.next_event:
            case GameEventType.TSUMO:
                if self.tile_deck.tiles_remaining == 0:
                    self.end_round_as_draw()
                    return
                await self.do_tsumo(previous_event_type=previous_turn_type)
            case GameEventType.DISCARD:
                if discarded_tile is None:
                    raise ValueError(
                        "[GameHand.get_possible_chii_actions]tile is none",
                    )
                await self.do_discard(
                    previous_turn_type=previous_turn_type,
                    discarded_tile=discarded_tile,
                )
            case GameEventType.ROBBING_KONG:
                if previous_action is None:
                    raise ValueError(
                        "[GameHand.get_possible_chii_actions]action is none",
                    )
                await self.do_robbing_kong(
                    robbing_tile=previous_action.tile,
                )
            case _:
                raise ValueError(
                    "[RoundManager.proceed_next_turn] Invalid next turn type.",
                )

    async def do_robbing_kong(
        self,
        robbing_tile: GameTile,
    ) -> GameEvent | None:
        self.set_winning_conditions(
            winning_tile=robbing_tile,
            previous_event_type=GameEventType.SHOMIN_KAN,
        )
        actions_lists: list[list[Action]] = self.check_actions_after_shomin_kong()
        return await self.send_actions_and_wait(actions_lists=actions_lists)

    def check_actions_after_shomin_kong(self) -> list[list[Action]]:
        result: list[list[Action]] = [[] for _ in range(GameManager.MAX_PLAYERS)]
        for player_seat in AbsoluteSeat:
            if player_seat == self.current_player_seat:
                continue
            result[player_seat].extend(
                self.get_possible_hu_choices(player_seat=player_seat),
            )
        return result

    # TODO event queue를 해 action을 처리하는 방식으로 바꾸기
    async def do_discard(
        self,
        previous_turn_type: GameEventType,
        discarded_tile: GameTile,
    ) -> GameEvent | None:
        self.hands[self.current_player_seat].apply_discard(discarded_tile)
        self.visible_tiles_count[discarded_tile] += 1
        self.set_winning_conditions(
            winning_tile=discarded_tile,
            previous_event_type=previous_turn_type,
        )

        actions_lists: list[list[Action]] = self.check_actions_after_discard()
        return await self.send_actions_and_wait(actions_lists=actions_lists)

    def check_actions_after_discard(self) -> list[list[Action]]:
        """
        Discard 후 가능한 Action들을 확인

        Returns:
            list[list[Action]]: Discard 후 가능한 Action들의 플레이어별 list,
            lst[player_absolute_seat_index]로 해당 플레이어의 Action list에
            접근가능
        """
        result: list[list[Action]] = [[] for _ in range(GameManager.MAX_PLAYERS)]
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
        actions_lists: list[list[Action]],
    ) -> GameEvent | None:
        self.game_manager.increase_action_id()
        for seat in AbsoluteSeat:
            if actions_lists[seat]:
                await self._send_discard_message(
                    seat=seat,
                    actions=actions_lists[seat],
                )

        pending_players, remaining_time = await self._initialize_pending_players(
            actions_lists=actions_lists,
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
            if response_event is not None:
                await self.send_response_action_event(response_action=response_event)
            return response_event
        return None

    async def _send_discard_message(
        self,
        seat: AbsoluteSeat,
        actions: list[Action],
    ) -> None:
        message = {
            "event": MessageEventType.DISCARD_ACTIONS,
            "actions": actions,
            "action_id": self.game_manager.action_id,
        }
        player: Player = self.game_manager.player_list[self.seat_to_player_index[seat]]
        await self.game_manager.network_service.send_personal_message(
            message=message,
            game_id=self.game_manager.game_id,
            user_id=player.uid,
        )

    async def _initialize_pending_players(
        self,
        actions_lists: list[list[Action]],
    ) -> tuple[set[AbsoluteSeat], dict[AbsoluteSeat, float]]:
        pending_players: set[AbsoluteSeat] = set()
        remaining_time: dict[AbsoluteSeat, float] = {}
        for seat in AbsoluteSeat:
            if actions_lists[seat]:
                pending_players.add(seat)
                remaining_time[seat] = self.DEFAULT_TURN_TIMEOUT
                await self._send_discard_message(
                    seat,
                    actions_lists[seat],
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

    def move_current_player_seat_to_next(
        self,
        previous_action: Action | None = None,
    ) -> None:
        """
        현재 턴이 수행되고 있는 절대 자리를 다음 턴이 수행될 자리로 이동시킴

        Args:
            previous_action (Action | None): 이전 액션 (None이면 Discard). Action이
            수행되었다면 Action의 상대 좌표에 따라 포커싱하고 있는 자리 이동
        """
        if previous_action is None:
            self.current_player_seat = self.current_player_seat.next_seat
        else:
            self.current_player_seat = self.current_player_seat.next_seat_after_action(
                action=previous_action,
            )

    def end_round_as_draw(self) -> None:
        """
        Round를 유국으로 종료

        이 메서드는 추후 구현되어야 함
        """
        # TODO: 유국 처리 로직 구현
        pass

    def check_actions_after_tsumo(self) -> list[list[Action]]:
        """
        Tsumo 후 가능한 Action들을 확인

        Returns:
            list[list[Action]]: Tsumo 후 가능한 Action들의 플레이어별 list,
            lst[player_absolute_seat_index]로 해당 플레이어의 Action list에 접근가능
        """
        result: list[list[Action]] = [[] for _ in range(GameManager.MAX_PLAYERS)]
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
            >= GameManager.MINIMUM_HU_SCORE
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

    async def send_tsumo_actions_and_wait_api(
        self,
        actions_lists: list[list[Action]],
    ) -> GameEvent:
        self.game_manager.increase_action_id()
        if actions_lists[self.current_player_seat]:
            message: dict[str, Any] = {
                "event": MessageEventType.TSUMO_ACTIONS,
                "actions": actions_lists[self.current_player_seat],
                "action_id": self.game_manager.action_id,
            }
            await self.game_manager.network_service.send_personal_message(
                message=message,
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
        self.game_manager.event_queue.task_done()
        elapsed_time  # 나중에 추가시간 관리에 쓸 예정
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
                data={
                    "tile": rightmost_tile,
                },
            )
        self.game_manager.increase_action_id()
        # await self.send_response_event(
        #     response_action=response_event,
        # )
        # self.apply_response_event(response_event=response_event)
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
        elapsed_time  # 나중에 추가시간 관리에 쓸 예정
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
                data={
                    "tile": rightmost_tile,
                },
            )
        self.game_manager.increase_action_id()
        return response_event

    # TODO
    async def do_action(self, current_event: GameEvent) -> RoundState:
        await self.send_response_action_event(
            response_action=current_event,
        )
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

    # TODO 각종 GameEventType에 대응하는 apply 추가
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
                self.hands[response_event.player_seat].apply_call(
                    block=CallBlock.create_from_game_event(
                        game_event=response_event,
                        current_seat=self.current_player_seat,
                        source_tile=self.winning_conditions.winning_tile,
                    ),
                )
                self.current_player_seat = response_event.player_seat

    async def send_response_action_event(
        self,
        response_action: GameEvent,
    ) -> None:
        match response_action.event_type:
            case GameEventType.FLOWER:
                await self.game_manager.network_service.broadcast(
                    message={
                        "event": MessageEventType.FLOWER,
                        "player_seat": response_action.player_seat,
                        "tile": None,
                    },
                    game_id=self.game_manager.game_id,
                )
            case GameEventType.AN_KAN:
                await self.game_manager.network_service.send_personal_message(
                    message={
                        "event": MessageEventType.AN_KAN,
                        "player_seat": response_action.player_seat,
                        "tile": response_action.data["tile"],
                    },
                    game_id=self.game_manager.game_id,
                    user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_action.player_seat]
                    ].uid,
                )
                await self.game_manager.network_service.broadcast(
                    message={
                        "event": MessageEventType.AN_KAN,
                        "player_seat": response_action.player_seat,
                        "tile": None,
                    },
                    game_id=self.game_manager.game_id,
                    exclude_user_id=self.game_manager.player_list[
                        self.seat_to_player_index[response_action.player_seat]
                    ].uid,
                )
                # await self.do_ankan
            case GameEventType.DISCARD:
                self.hands[self.current_player_seat].apply_discard(
                    tile=response_action.data["tile"],
                )
                await self.game_manager.network_service.broadcast(
                    message={
                        "event": MessageEventType.DISCARD,
                        "tile": response_action.data["tile"],
                    },
                    game_id=self.game_manager.game_id,
                )

    def set_winning_conditions(
        self,
        winning_tile: GameTile,
        previous_event_type: GameEventType,
    ) -> None:
        """
        현재 포커싱된 화료패 후보와 이전 TurnType에 따라 WinningCondition을 설정함

        Args:
            winning_tile (GameTile): 화료패 후보
            previous_turn_type (TurnType): 이전 턴의 타입
        """
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
        drawn_tiles: list[GameTile]
        if self.tile_deck.HAIPAI_TILES < 1:
            raise ValueError(
                "Not enough tiles remaining. "
                "Requested: {1}, Available: {self.tile_deck.HAIPAI_TILES}",
            )
        if previous_event_type.is_next_replacement:
            drawn_tiles = self.tile_deck.draw_tiles_right(1)
        else:
            drawn_tiles = self.tile_deck.draw_tiles(1)
        self.hands[self.current_player_seat].apply_tsumo(
            tile=drawn_tiles[0],
        )
        self.set_winning_conditions(
            winning_tile=drawn_tiles[0],
            previous_event_type=previous_event_type,
        )
        actions_lists: list[list[Action]] = self.check_actions_after_tsumo()
        return await self.send_tsumo_actions_and_wait_api(
            actions_lists=actions_lists,
        )


class GameManager:
    MINIMUM_HU_SCORE: Final[int] = 8
    MAX_PLAYERS: Final[int] = 4
    TOTAL_ROUNDS: Final[int] = 16

    def __init__(
        self,
        game_id: int,
        room_manager: RoomManager = Depends(get_room_manager()),
        network_service: NetworkService = Depends(get_network_service()),
    ) -> None:
        self.game_id: int = game_id
        self.room_manager: RoomManager = room_manager
        self.network_service: NetworkService = network_service
        self.player_list: list[Player]
        self.player_uid_to_index: dict[str, int]
        self.round_manager: RoundManager
        self.current_round: Round
        self.action_id: int
        self.event_queue: asyncio.Queue[GameEvent]

    def init_game(self, player_datas: list[PlayerData]) -> None:
        if len(player_datas) != GameManager.MAX_PLAYERS:
            raise ValueError(
                f"[GameManager] {GameManager.MAX_PLAYERS} players needed, "
                f"{len(player_datas)} players received",
            )
        self.player_list = []
        shuffle(player_datas)
        for index, player_data in enumerate(player_datas):
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
        for _ in range(self.TOTAL_ROUNDS):
            await self.round_manager.run_round()
        await self.submit_game_result()

    # TODO submit game result to core sever
    async def submit_game_result(self) -> None:
        pass

    def get_valid_discard_result(
        self,
        uid: str,
        tile: GameTile,
    ) -> dict[str, AbsoluteSeat]:
        player_seat: AbsoluteSeat = self.round_manager.player_index_to_seat[
            self.player_uid_to_index[uid]
        ]
        return (
            {"seat": player_seat}
            if tile in self.round_manager.hands[player_seat].tiles
            else {}
        )

    async def enqueue_event(self, event: GameEvent) -> None:
        try:
            await self.event_queue.put(event)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"Failed to enqueue event: {e}")

    def increase_action_id(self) -> None:
        self.action_id += 1


class ActionManager:
    def __init__(self, action_list: list[Action]):
        """
        ActionManager 인스턴스 초기화

        Args:
            action_list (list[Action]): 전체 Action 리스트
        """
        self.action_heap: list[Action] = action_list
        heapq.heapify(self.action_heap)
        self.selected_action_heap: list[Action] = []
        self.finished_players: set[RelativeSeat] = set()
        self.final_action: Action | None = None

    def empty(self) -> bool:
        """
        Action heap이 비었는지 여부를 반환

        Returns:
            bool: Action heap이 비었으면 True, 아니면 False
        """
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
