# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App info
    APP_NAME: str
    APP_VERSION: str

    # LLM API
    OPENAI_API_KEY: str

    # PostgreSQL Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    class Config:
        env_file = ".env"

# Singleton instance
settings = Settings()

def get_settings() -> Settings:
    return settings

