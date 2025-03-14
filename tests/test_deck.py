from app.services.game_manager.models.deck import Deck


def test_shuffle_deck():
    deck = Deck()
    original = deck.tiles.copy()
    deck._shuffle_deck()
    assert sorted(deck.tiles) == sorted(original)
