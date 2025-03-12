from fastapi import APIRouter

from app.api.v1.endpoints import score_check

api_router = APIRouter()
api_router.include_router(score_check.router, tags=["score-check"])
