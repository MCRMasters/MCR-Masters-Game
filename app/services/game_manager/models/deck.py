from secrets import randbelow
from typing import Final

from app.services.game_manager.models.enums import GameTile


class Deck:
    TOTAL_TILES: Final[int] = 144
    HAIPAI_TILES: Final[int] = 13

    def __init__(self) -> None:
        self.tiles: list[GameTile]
        self.draw_index_left: int = 0
        self.draw_index_right: int = Deck.TOTAL_TILES
        self._make_deck()

    def _make_deck(self) -> None:
        self.tiles = [GameTile(tile) for tile in GameTile.normal_tiles()] * 4 + [
            GameTile(flower_tile) for flower_tile in GameTile.flower_tiles()
        ]
        self._shuffle_deck()

    def _shuffle_deck(self) -> None:
        # Fisher-Yates shuffle with secrets.randbelow
        for i in range(len(self.tiles) - 1, 0, -1):
            j = randbelow(i + 1)
            self.tiles[i], self.tiles[j] = self.tiles[j], self.tiles[i]

    @property
    def tiles_left(self) -> int:
        return self.draw_index_right - self.draw_index_left

    def draw_tiles(self, count: int) -> list[GameTile] | None:
        remaining: int = self.tiles_left
        if remaining < count:
            return None
        drawn_tiles: list[GameTile] = self.tiles[
            self.draw_index_left : self.draw_index_left + count
        ]
        self.draw_index_left += count
        return drawn_tiles

    def draw_tiles_right(self, count: int) -> list[GameTile] | None:
        remaining: int = self.tiles_left
        if remaining < count:
            return None
        drawn_tiles: list[GameTile] = self.tiles[
            self.draw_index_right - count : self.draw_index_right
        ]
        self.draw_index_right -= count
        return drawn_tiles

    def draw_haipai(self) -> list[GameTile]:
        tiles = self.draw_tiles(Deck.HAIPAI_TILES)
        if tiles is None:
            raise ValueError("Not enough tiles in the deck to draw haipai")
        return tiles
