import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str
    
    # OpenAI Configuration (commented out, available as fallback)
    # OPENAI_API_KEY: str
    # OPENAI_MODEL: str = "gpt-4-turbo-preview"
    # OPENAI_MAX_TOKENS: int = 4000
    # OPENAI_TEMPERATURE: float = 0.7
    
    # Gemini Configuration (primary AI engine)
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-pro"
    GEMINI_MAX_TOKENS: int = 4000
    GEMINI_TEMPERATURE: float = 0.7
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./family_guardian.db"
    
    # Redis Configuration (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379"
    
    # MCP Server Configuration
    MCP_SERVER_URL: Optional[str] = None
    MCP_SERVER_TOKEN: Optional[str] = None
    
    # Memory Configuration
    MEMORY_FILE_PATH: str = "./memory/relationship_context.json"
    MAX_MEMORY_ENTRIES: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/bot.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 