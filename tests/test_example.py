from app.score_calculator.hand.hand import Hand


def test_sample():
    assert True


def print_hand(hand1: Hand):
    print(hand1)


def test_print_output():
    print_hand(Hand([0] * 34, []))
    print_hand(Hand.create_from_tiles([0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8], []))
    assert True
