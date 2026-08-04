import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Diamond Selling Intelligence Platform"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
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

