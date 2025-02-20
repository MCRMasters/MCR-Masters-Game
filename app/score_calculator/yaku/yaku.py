# yaku.py
from typing import List, Dict, Callable
from block import Block, BlockType
from hand import WinningCondition
from app.score_calculator.yaku.check import *

# 야쿠 함수 타입 (예: index, blocks, used_flag, checked_yaku, winning_condition)
YakuFunction = Callable[[int, List[Block], List[int], Dict[int, int], WinningCondition], int]


# YAKU_LIST에 ("ChickenHand", chicken_hand)를 첫 번째 요소로 넣고, 이후에 아래 79개 야쿠 이름을 추가합니다.
YAKU_LIST = [
    ("ChickenHand", chicken_hand),
    ("Chained Seven Pairs", chained_seven_pairs),
    ("Thirteen Orphans", thirteen_orphans),
    ("Big Four Winds", big_four_winds),
    ("Big Three Dragons", big_three_dragons),
    ("Nine Gates", nine_gates),
    ("All Green", all_green),
    ("Four Quads", four_quads),
    ("Four Concealed Pungs", four_concealed_pungs),
    ("All Terminals", all_terminals),
    ("Little Four Winds", little_four_winds),
    ("Little Three Dragons", little_three_dragons),
    ("All Honors", all_honors),
    ("Pure Terminal Chows", pure_terminal_chows),
    ("Quadruple Chow", quadruple_chow),
    ("Four Pure Shifted Pungs", four_pure_shifted_pungs),
    ("Four Pure Shifted Chows", four_pure_shifted_chows),
    ("Three Kongs", three_kongs),
    ("All Terminals And Honors", all_terminals_and_honors),
    ("Seven Pairs", seven_pairs),
    ("Greater Honors And Knitted Tiles", greater_honors_and_knitted_tiles),
    ("All Even Pungs", all_even_pungs),
    ("Full Flush", full_flush),
    ("Upper Tiles", upper_tiles),
    ("Middle Tiles", middle_tiles),
    ("Lower Tiles", lower_tiles),
    ("Pure Triple Chow", pure_triple_chow),
    ("Pure Shifted Pungs", pure_shifted_pungs),
    ("Pure Straight", pure_straight),
    ("Three Suited Terminal Chows", three_suited_terminal_chows),
    ("Pure Shifted Chows", pure_shifted_chows),
    ("All Fives", all_fives),
    ("Triple Pung", triple_pung),
    ("Three Concealed Pungs", three_concealed_pungs),
    ("Lesser Honors And Knitted Tiles", lesser_honors_and_knitted_tiles),
    ("Knitted Straight", knitted_straight),
    ("Upper Four", upper_four),
    ("Lower Four", lower_four),
    ("Big Three Winds", big_three_winds),
    ("Last Tile Draw", last_tile_draw),
    ("Last Tile Claim", last_tile_claim),
    ("Out With Replacement Tile", out_with_replacement_tile),
    ("Robbing The Kong", robbing_the_kong),
    ("Mixed Straight", mixed_straight),
    ("Mixed Triple Chow", mixed_triple_chow),
    ("Reversible Tiles", reversible_tiles),
    ("Mixed Shifted Pungs", mixed_shifted_pungs),
    ("Two Concealed Kongs", two_concealed_kongs),
    ("Melded Hand", melded_hand),
    ("Mixed Shifted Chows", mixed_shifted_chows),
    ("All Pungs", all_pungs),
    ("Half Flush", half_flush),
    ("All Types", all_types),
    ("Two Dragons", two_dragons),
    ("Fully Concealed Hand", fully_concealed_hand),
    ("Last Tile", last_tile),
    ("Outside Hand", outside_hand),
    ("Two Melded Kongs", two_melded_kongs),
    ("Concealed Hand", concealed_hand),
    ("Dragon Pung", dragon_pung),
    ("Prevalent Wind", prevalent_wind),
    ("Seat Wind", seat_wind),
    ("All Chows", all_chows),
    ("Double Pung", double_pung),
    ("Two Concealed Pungs", two_concealed_pungs),
    ("Tile Hog", tile_hog),
    ("Concealed Kong", concealed_kong),
    ("All Simples", all_simples),
    ("Pure Double Chow", pure_double_chow),
    ("Mixed Double Chow", mixed_double_chow),
    ("Short Straight", short_straight),
    ("Two Terminal Chows", two_terminal_chows),
    ("Pung Of Terminals Or Honors", pung_of_terminals_or_honors),
    ("One Voided Suit", one_voided_suit),
    ("No Honors", no_honors),
    ("Single Wait", single_wait),
    ("Melded Kong", melded_kong),
    ("Self Drawn", self_drawn),
    ("Edge Wait", edge_wait),
    ("Closed Wait", closed_wait),
]


# 야쿠 매핑 사전
yaku_map = {f"YakuCheck_{name}": i for i, (name, func) in enumerate(YAKU_LIST)}
inverse_yaku_map = {i: f"YakuCheck_{name}" for i, (name, func) in enumerate(YAKU_LIST)}
yaku_functions = {i: func for i, (name, func) in enumerate(YAKU_LIST)}

def get_score_general(blocks: List[Block], winning_condition: WinningCondition) -> Dict[int, int]:
    """
    주어진 블록들에 대해 각 야쿠별 점수를 계산하는 간단한 예시 함수.
    실제 구현에서는 복잡한 재귀/반복 로직이 들어갑니다.
    """
    scores = {}
    # 각 야쿠 함수를 호출하여 점수를 산출
    for yaku_id, func in yaku_functions.items():
        score = func(0, blocks, [0] * len(blocks), {}, winning_condition)
        if score:
            scores[yaku_id] = score
    return scores