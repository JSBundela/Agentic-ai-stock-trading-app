from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Agentic AI Stock Trading Platform"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Kotak Credentials
    KOTAK_ACCESS_TOKEN: str | None = None
    
    MOBILE_NUMBER: str
    UCC: str
    MPIN: str
    
    # URLs
    KOTAK_TRADE_API_URL: str = "https://mis.kotaksecurities.com"

    # Agentic AI
    GROQ_API_KEY: str | None = None  # FREE Groq API
    OPENROUTER_API_KEY: str | None = None  # Fallback (requires credits)

    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings():
    return Settings()
