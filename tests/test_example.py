from app.score_calculator.divide.general_shape import (
    divide_general_shape,
    divide_general_shape_knitted_sub,
)
from app.score_calculator.hand.hand import Hand
from tests.test_utils import print_blocks, raw_string_to_hand_class


def test_sample():
    assert True


def print_hand(hand1: Hand):
    print(hand1)


def test_print_output():
    print_hand(Hand([0] * 34, []))
    print_hand(Hand.create_from_tiles([0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8], []))
    assert True


def test_print_string_to_hand_1():
    print_hand(raw_string_to_hand_class("1112345678999m9m"))
    print_hand(raw_string_to_hand_class("123m123p123s777z11z"))
    print_hand(raw_string_to_hand_class("123m123p123s11z[888p]"))
    print_hand(raw_string_to_hand_class("123m[888p]123p123s11z"))
    assert True


def test_general_hand_parse():
    hand = raw_string_to_hand_class("1112345678999m9m")
    print(hand)
    for blocks in divide_general_shape(hand):
        print_blocks(blocks)
    hand = raw_string_to_hand_class("147m258s369p111m11z")
    print(hand)
    for blocks in divide_general_shape_knitted_sub(hand):
        print_blocks(blocks)
    assert True
