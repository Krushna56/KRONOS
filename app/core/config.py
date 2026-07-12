# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     APP_NAME: str = "AI Clone"
#     APP_ENV: str = "development"

#     DATABASE_URL: str = "DATABASE_URL: str = "postgresql+asyncpg://postgres:Ai%405605@localhost:5432/aiclone"
#     REDIS_URL: str = "redis://localhost:6379"

#     JWT_SECRET: str = "mysecretkey"
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

#     model_config = {
#         "env_file": ".env",
#         "env_file_encoding": "utf-8",
#         "extra": "ignore"
#     }

# settings = Settings()

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")


class Settings(BaseSettings):

    APP_NAME: str
    APP_ENV: str

    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET: str

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()


