from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel


# 필요한 필드 추후 추가
@dataclass
class Player:
    uid: str
    nickname: str
    index: int
    score: int

    @staticmethod
    def create_from_received_data(
        player_data: PlayerData,
        index: int,
    ) -> Player:
        return Player(
            uid=player_data.uid,
            nickname=player_data.nickname,
            index=index,
            score=0,
        )


# Core Server에서 넘어오는 정보에 따라 필드 추후 추가, 필요시 schema로 이동
class PlayerData(BaseModel):
    uid: str
    nickname: str
