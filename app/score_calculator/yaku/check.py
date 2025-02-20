# yaku.py
from typing import List, Dict, Callable
from block import Block, BlockType
from hand import WinningCondition


# 각 야쿠 함수들은 미리 구현되어 있다고 가정합니다.
# 예시 함수 이름들은 아래와 같이 사용합니다.
def chicken_hand(index: int, blocks: List[Block], used_flag: List[int],
                      checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def chained_seven_pairs(index: int, blocks: List[Block], used_flag: List[int],
                             checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def thirteen_orphans(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def big_four_winds(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def big_three_dragons(index: int, blocks: List[Block], used_flag: List[int],
                           checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def nine_gates(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_green(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def four_quads(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def four_concealed_pungs(index: int, blocks: List[Block], used_flag: List[int],
                              checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_terminals(index: int, blocks: List[Block], used_flag: List[int],
                       checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def little_four_winds(index: int, blocks: List[Block], used_flag: List[int],
                           checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def little_three_dragons(index: int, blocks: List[Block], used_flag: List[int],
                              checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_honors(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pure_terminal_chows(index: int, blocks: List[Block], used_flag: List[int],
                             checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def quadruple_chow(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def four_pure_shifted_pungs(index: int, blocks: List[Block], used_flag: List[int],
                                 checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def four_pure_shifted_chows(index: int, blocks: List[Block], used_flag: List[int],
                                 checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def three_kongs(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_terminals_and_honors(index: int, blocks: List[Block], used_flag: List[int],
                                  checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def seven_pairs(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def greater_honors_and_knitted_tiles(index: int, blocks: List[Block], used_flag: List[int],
                                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_even_pungs(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def full_flush(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def upper_tiles(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def middle_tiles(index: int, blocks: List[Block], used_flag: List[int],
                      checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def lower_tiles(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pure_triple_chow(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pure_shifted_pungs(index: int, blocks: List[Block], used_flag: List[int],
                            checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pure_straight(index: int, blocks: List[Block], used_flag: List[int],
                       checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def three_suited_terminal_chows(index: int, blocks: List[Block], used_flag: List[int],
                                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pure_shifted_chows(index: int, blocks: List[Block], used_flag: List[int],
                            checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_fives(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def triple_pung(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def three_concealed_pungs(index: int, blocks: List[Block], used_flag: List[int],
                               checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def lesser_honors_and_knitted_tiles(index: int, blocks: List[Block], used_flag: List[int],
                                         checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def knitted_straight(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def upper_four(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def lower_four(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def big_three_winds(index: int, blocks: List[Block], used_flag: List[int],
                         checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def last_tile_draw(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def last_tile_claim(index: int, blocks: List[Block], used_flag: List[int],
                         checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def out_with_replacement_tile(index: int, blocks: List[Block], used_flag: List[int],
                                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def robbing_the_kong(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def mixed_straight(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def mixed_triple_chow(index: int, blocks: List[Block], used_flag: List[int],
                           checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def reversible_tiles(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def mixed_shifted_pungs(index: int, blocks: List[Block], used_flag: List[int],
                             checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def two_concealed_kongs(index: int, blocks: List[Block], used_flag: List[int],
                             checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def melded_hand(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def mixed_shifted_chows(index: int, blocks: List[Block], used_flag: List[int],
                             checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_pungs(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def half_flush(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_types(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def two_dragons(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def fully_concealed_hand(index: int, blocks: List[Block], used_flag: List[int],
                              checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def last_tile(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def outside_hand(index: int, blocks: List[Block], used_flag: List[int],
                      checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def two_melded_kongs(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def concealed_hand(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def dragon_pung(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def prevalent_wind(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def seat_wind(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_chows(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def double_pung(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def two_concealed_pungs(index: int, blocks: List[Block], used_flag: List[int],
                             checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def tile_hog(index: int, blocks: List[Block], used_flag: List[int],
                  checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def concealed_kong(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def all_simples(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pure_double_chow(index: int, blocks: List[Block], used_flag: List[int],
                          checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def mixed_double_chow(index: int, blocks: List[Block], used_flag: List[int],
                           checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def short_straight(index: int, blocks: List[Block], used_flag: List[int],
                        checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def two_terminal_chows(index: int, blocks: List[Block], used_flag: List[int],
                            checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def pung_of_terminals_or_honors(index: int, blocks: List[Block], used_flag: List[int],
                                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def one_voided_suit(index: int, blocks: List[Block], used_flag: List[int],
                         checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def no_honors(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def single_wait(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def melded_kong(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def self_drawn(index: int, blocks: List[Block], used_flag: List[int],
                    checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def edge_wait(index: int, blocks: List[Block], used_flag: List[int],
                   checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0

def closed_wait(index: int, blocks: List[Block], used_flag: List[int],
                     checked_yaku: Dict[int, int], winning_condition: WinningCondition) -> int:
    return 0
