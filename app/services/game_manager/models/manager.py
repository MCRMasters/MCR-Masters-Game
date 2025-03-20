from __future__ import annotations

import heapq
from collections import Counter
from random import shuffle
from typing import Final

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.deck import Deck
from app.services.game_manager.models.enums import (
    AbsoluteSeat,
    GameTile,
    RelativeSeat,
    Round,
)
from app.services.game_manager.models.hand import GameHand
from app.services.game_manager.models.player import (
    Player,
    PlayerData,
)
from app.services.game_manager.models.types import ActionType, TurnType
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

    def init_round(self) -> None:
        """
        round 초기화를 수행

        패산, 손패, default Winning Condition 등 Round에 필요한 기본 데이터들을 설정
        """
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

    def start_round(self) -> None:
        """
        Round의 진입점

        배패의 화패를 빼는것으로부터 시작
        """
        self.do_flower_action_in_init_hand()

    # TODO
    def do_flower_action_in_init_hand(self) -> None:
        """
        배패의 화패를 동->남->서->북 순으로 전부 빼는 함수

        이후 self.do_tsumo()로 진입
        """
        pass

    def proceed_next_turn(
        self,
        previous_turn_type: TurnType,
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
        match previous_turn_type.next_turn:
            case TurnType.TSUMO:
                if self.tile_deck.tiles_remaining == 0:
                    self.end_round_as_draw()
                    return
                self.do_tsumo(previous_turn_type=previous_turn_type)
            case TurnType.DISCARD:
                if discarded_tile is None:
                    raise ValueError(
                        "[GameHand.get_possible_chii_actions]tile is none",
                    )
                self.do_discard(
                    previous_turn_type=previous_turn_type,
                    discarded_tile=discarded_tile,
                )
            case TurnType.ROBBING_KONG:
                if previous_action is None:
                    raise ValueError(
                        "[GameHand.get_possible_chii_actions]action is none",
                    )
                self.do_robbing_kong(
                    previous_turn_type=previous_turn_type,
                    robbing_tile=previous_action.tile,
                )
            case _:
                raise ValueError(
                    "[RoundManager.proceed_next_turn] Invalid next turn type.",
                )

    def do_robbing_kong(
        self,
        previous_turn_type: TurnType,
        robbing_tile: GameTile,
    ) -> None:
        self.set_winning_conditions(
            winning_tile=robbing_tile,
            previous_turn_type=previous_turn_type,
        )
        actions_lists: list[list[Action]] = self.check_actions_after_shomin_kong()
        self.send_actions_and_wait_api(actions_lists=actions_lists)

    def check_actions_after_shomin_kong(self) -> list[list[Action]]:
        result: list[list[Action]] = [[] for _ in range(GameManager.MAX_PLAYERS)]
        for player_seat in AbsoluteSeat:
            if player_seat == self.current_player_seat:
                continue
            result[player_seat].extend(
                self.get_possible_hu_choices(player_seat=player_seat),
            )
        return result

    def do_discard(
        self,
        previous_turn_type: TurnType,
        discarded_tile: GameTile,
    ) -> None:
        """
        현재 턴에 Discard를 수행

        Args:
            previous_turn_type (TurnType): 이전 턴의 타입
        """
        self.hands[self.current_player_seat].apply_discard(discarded_tile)
        self.visible_tiles_count[discarded_tile] += 1
        self.set_winning_conditions(
            winning_tile=discarded_tile,
            previous_turn_type=previous_turn_type,
        )

        actions_lists: list[list[Action]] = self.check_actions_after_discard()
        self.send_actions_and_wait_api(actions_lists=actions_lists)

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

    def send_actions_and_wait_api(
        self,
        actions_lists: list[list[Action]],
    ) -> None:
        """
        Discard/Robbing Kong 후 Action들을 플레이어에게 전송하고 응답을 대기

        이 메서드는 추후 구현되어야 함
        """
        # TODO: Discard와 그에 따른 Action list 전송 및 Action 선택 대기 로직 구현
        # Discard에 따른 Action은 timeout후 강제 진행을 고려해줘야 함
        pass

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

    # TODO
    def send_tsumo_actions_and_wait_api(
        self,
        actions_lists: list[list[Action]],
    ) -> None:
        """
        Tsumo 후 수행 가능한 Action list 플레이어에게 전송하고 응답을 대기

        이 메서드는 추후 구현되어야 함
        """
        # TODO: Tsumo와 수행 가능한 Action 전송 및 대기 로직 구현
        # Discard와는 다르게 강제 진행하지 않아도 됨(타패 타이머와 Time을 공유하며
        # action wait에 대한 timeout은 별도로 없음)
        pass

    def set_winning_conditions(
        self,
        winning_tile: GameTile,
        previous_turn_type: TurnType,
    ) -> None:
        """
        현재 포커싱된 화료패 후보와 이전 TurnType에 따라 WinningCondition을 설정함

        Args:
            winning_tile (GameTile): 화료패 후보
            previous_turn_type (TurnType): 이전 턴의 타입
        """
        self.winning_conditions.winning_tile = winning_tile
        self.winning_conditions.is_discarded = previous_turn_type.is_next_discard
        self.winning_conditions.is_last_tile_of_its_kind = (
            self.visible_tiles_count.get(winning_tile, 0) == 3
        )
        self.winning_conditions.is_last_tile_in_the_game = (
            self.tile_deck.tiles_remaining == 0
        )
        self.winning_conditions.is_replacement_tile = previous_turn_type.is_kong
        self.winning_conditions.is_robbing_the_kong = (
            previous_turn_type == TurnType.SHOMIN_KAN
        )

    def do_tsumo(self, previous_turn_type: TurnType) -> None:
        """
        현재 플레이어의 Tsumo 액션을 수행함

        이전 TurnType에 따라 패산의 왼쪽 또는 오른쪽에서 타일을 뽑음 뽑은 타일을
        현재 플레이어의 손패에 추가하고, Winning Condition을 설정한 후 가능한 action
        list들을 확인하고 플레이어에게 전송

        Args:
            previous_turn_type (TurnType): 이전 턴의 타입
        """
        drawn_tiles: list[GameTile]
        if self.tile_deck.HAIPAI_TILES < 1:
            raise ValueError(
                "Not enough tiles remaining. "
                "Requested: {1}, Available: {self.tile_deck.HAIPAI_TILES}",
            )
        if previous_turn_type.is_next_replacement:
            drawn_tiles = self.tile_deck.draw_tiles_right(1)
        else:
            drawn_tiles = self.tile_deck.draw_tiles(1)
        self.hands[self.current_player_seat].apply_tsumo(
            tile=drawn_tiles[0],
        )
        self.set_winning_conditions(
            winning_tile=drawn_tiles[0],
            previous_turn_type=previous_turn_type,
        )
        actions_lists: list[list[Action]] = self.check_actions_after_tsumo()
        self.send_tsumo_actions_and_wait_api(actions_lists=actions_lists)


class GameManager:
    MINIMUM_HU_SCORE: Final[int] = 8
    MAX_PLAYERS: Final[int] = 4

    def __init__(self) -> None:
        self.player_list: list[Player]
        self.player_uid_to_index: dict[str, int]
        self.round_manager: RoundManager
        self.current_round: Round
        self.action_id: int

    def init_game(self, player_datas: list[PlayerData]) -> None:
        """
        주어진 플레이어 데이터를 이용해 게임을 초기화

        Args:
            player_datas (list[PlayerDataReceived]): Core Server에서 받은
                플레이어 데이터 리스트
        """
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
        self.round_manager.init_round()
        self.current_round = Round.E1
        self.action_id = 0

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

    def start_game(self) -> None:
        self.round_manager.start_round()

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
