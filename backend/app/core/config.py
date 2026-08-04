import json
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


def parse_cors_origins(value: str | List[str] | None) -> List[str]:
    """Accept Railway/Vercel-friendly JSON or comma-separated CORS origins."""
    if not value:
        return ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(origin).strip() for origin in parsed if str(origin).strip()]
    except json.JSONDecodeError:
        pass
    return [origin.strip() for origin in value.split(",") if origin.strip()]

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Diamond Selling Intelligence Platform"
    # Keep this as a string so Railway accepts either a JSON array or one URL.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    # Public users can view dashboards; shared data changes require this secret.
    ADMIN_API_KEY: str = ""
    
    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    # Selling Engine Thresholds (Configurable)
    PREMIUM_THRESHOLD_PCT: float = 15.0  # >= 15% -> Premium Opportunity
    SELL_NOW_THRESHOLD_PCT: float = 10.0 # 10% - 15% -> Sell Now
    GOOD_OPP_THRESHOLD_PCT: float = 5.0  # 5% - 10% -> Good Opportunity
    WAIT_THRESHOLD_PCT: float = 3.0      # 3% - 5% -> Wait
    # Below 3% -> Avoid

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

settings = Settings()
settings.CORS_ORIGINS = parse_cors_origins(settings.CORS_ORIGINS)

