"""Application Configuration Settings"""

from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    app_name: str = "Internal Testing Portal"
    debug: bool = True
    polling_interval_seconds: int = 3
    
    max_sessions: int = 5
    max_executions_per_session: int = 10
    storage_path: str = "storage"
    
    huggingface_api_key: str = ""
    huggingface_model: str = "gpt2"
    
    api_dev_url: str = "https://dev-api.insurance.com"
    api_qa_url: str = "https://qa-api.insurance.com"
    api_staging_url: str = "https://staging-api.insurance.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
