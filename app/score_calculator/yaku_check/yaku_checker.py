from abc import ABC, abstractmethod

from app.score_calculator.enums.enums import Yaku


class YakuChecker(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def set_yaku(self) -> None:
        pass

    @property
    @abstractmethod
    def yaku(self) -> Yaku:
        pass
