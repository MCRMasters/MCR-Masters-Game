from pydantic import BaseModel


class WatchGameUser(BaseModel):
    uid: str
    nickname: str


class WatchGame(BaseModel):
    game_id: int
    start_time: str
    users: list[WatchGameUser]
