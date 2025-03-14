from dataclasses import dataclass


# 필요한 필드 추후 추가
@dataclass
class Player:
    uid: str
    index: int
    score: int
