from abc import ABC, abstractmethod

from app.services.score_calculator.enums.enums import Yaku


class YakuChecker(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def set_yakus(self) -> None:
        pass

    @property
    @abstractmethod
    def yakus(self) -> list[Yaku]:
        pass
