from fastapi import APIRouter

from app.api.v1.endpoints import game_ws, score_check, watch

api_router = APIRouter()
api_router.include_router(score_check.router, tags=["score-check"])
api_router.include_router(game_ws.router, tags=["game-ws"])
api_router.include_router(watch.router, tags=["watch"])
