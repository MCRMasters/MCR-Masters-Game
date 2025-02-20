# hand.py
import copy
from typing import List
from block import Block, BlockType, BlockSource
from utils import tile_num_to_string, tile_name_to_num
from yaku import get_score_general

class WinningCondition:
    def __init__(self, tile: int, is_discarded: bool = False,
                 is_last_tile_in_the_game: bool = False, is_last_tile_of_its_kind: bool = False,
                 is_replacement_tile: bool = False, is_robbing_the_kong: bool = False,
                 count_winning_conditions: int = 0, seat_wind: int = 0, round_wind: int = 0):
        self.tile = tile
        self.is_discarded = is_discarded
        self.is_last_tile_in_the_game = is_last_tile_in_the_game
        self.is_last_tile_of_its_kind = is_last_tile_of_its_kind
        self.is_replacement_tile = is_replacement_tile
        self.is_robbing_the_kong = is_robbing_the_kong
        self.count_winning_conditions = count_winning_conditions
        self.seat_wind = seat_wind
        self.round_wind = round_wind

class Hand:
    def __init__(self, closed_tiles: List[int] = None, opened_tiles: List[int] = None, call_blocks: List[Block] = None):
        self.closed_tiles = closed_tiles if closed_tiles is not None else [0] * 35
        self.opened_tiles = opened_tiles if opened_tiles is not None else [0] * 35
        self.call_blocks = call_blocks if call_blocks is not None else []
        self.winning_tile = -1
        self.is_blocks_divided = False
        self.yaku_score_list = {}  # 예: {yaku_id: score}
        self.highest_score = 0
        self.keishiki_tenpai_tiles = []  # 텐파이 가능한 타일 리스트

    def initialize_opened_tiles(self, call_blocks: List[Block]):
        self.opened_tiles = [0] * 35
        self.call_blocks = call_blocks
        for block in self.call_blocks:
            if block.type == BlockType.SEQUENCE:
                self.opened_tiles[block.tile] += 1
                self.opened_tiles[block.tile + 1] += 1
                self.opened_tiles[block.tile + 2] += 1
            elif block.type == BlockType.TRIPLET:
                self.opened_tiles[block.tile] += 3
            elif block.type == BlockType.QUAD:
                self.opened_tiles[block.tile] += 4

    def is_open(self) -> bool:
        return any(block.source != BlockSource.SELF for block in self.call_blocks)

    def divide_blocks(self, winning_condition: WinningCondition):
        """
        블록(세트) 분할 및 점수 계산 – 여기서는 단순화하여
        현재 call_blocks 기반으로 점수를 계산하는 예시를 보여줍니다.
        """
        blocks = copy.deepcopy(self.call_blocks)
        scores = get_score_general(blocks, winning_condition)
        if scores:
            self.highest_score = max(scores.values())
            self.yaku_score_list = scores
            self.is_blocks_divided = True
        else:
            self.is_blocks_divided = False

    def get_keishiki_tenpai_tiles(self):
        """
        텐파이 타일 목록을 계산합니다.
        (실제 구현은 손패를 하나씩 추가해보고 완성 여부를 검사하는 로직이 필요합니다.)
        """
        self.keishiki_tenpai_tiles.clear()
        for tile in range(34):
            self.closed_tiles[tile] += 1
            temp_condition = WinningCondition(tile)
            self.divide_blocks(temp_condition)
            if self.is_blocks_divided:
                self.keishiki_tenpai_tiles.append(tile)
            self.closed_tiles[tile] -= 1

    def print_score(self):
        print("Highest Score:", self.highest_score)
        for yaku_id, score in self.yaku_score_list.items():
            print(f"Yaku: {yaku_id} ({score})")

    def print_hand(self):
        print("[Closed Tiles]")
        for i, count in enumerate(self.closed_tiles):
            if count:
                print(f"{tile_num_to_string(i)}: {count}", end="  ")
        print("\n[Opened Tiles]")
        for i, count in enumerate(self.opened_tiles):
            if count:
                print(f"{tile_num_to_string(i)}: {count}", end="  ")
        print()
