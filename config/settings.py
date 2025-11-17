# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App info
    APP_NAME: str 
    APP_VERSION: str
    # LLM API (Groq / OpenAI)
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str
    GROQ_API_ENDPOINT: str
    GROQ_MAX_TOKENS: int 
    GROQ_TEMPERATURE: float 

    # PostgreSQL Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int 
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Backend URL that Streamlit will call
    API_URL: str 
    BACKEND_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()

def get_settings() -> Settings:
    return settings