from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    PROJECT_NAME: str = "MCR Game Server API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    SERVER_URL: str = "mcrs.duckdns.org:8001"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
