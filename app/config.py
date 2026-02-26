from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "OSIRA Wealth Agent"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_EXPIRE_SECONDS: int = 3600
    
    # Claude
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    
    # WhatsApp (Twilio)
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str
    
    # MCP Servers
    MCP_OPENFINANCE_URL: str = "http://localhost:3001"
    MCP_COMDINHEIRO_URL: str = "http://localhost:3002"
    MCP_B3_URL: str = "http://localhost:3003"
    
    # Pluggy (Open Finance)
    PLUGGY_CLIENT_ID: str
    PLUGGY_CLIENT_SECRET: str
    
    # ComDinheiro
    COMDINHEIRO_API_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
