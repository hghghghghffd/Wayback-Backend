from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./waygo.db"
    SECRET_KEY: str = "changeme-set-in-env"
    MOTHERSHIP_KEY: str = "changeme-set-in-env"
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["*"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    IP_BAN_THRESHOLD: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
