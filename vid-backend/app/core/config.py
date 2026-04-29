"""
app/core/config.py
Central configuration — reads from .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # App
    app_name: str = "VID — Virtual ID API"
    app_version: str = "1.0.0"
    app_env: str = "development"
    secret_key: str = "change_me_in_production"

    # Nokia NaC
    nokia_nac_token: str = ""

    # CORS — comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:3000"

    # Optional: Anthropic for AI explainer
    anthropic_api_key: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def use_mock_apis(self) -> bool:
        """
        Use mock CAMARA responses when Nokia NaC token is not set.
        In development this lets you build the full flow without credentials.
        Switch to False once you have real Nokia NaC credentials.
        """
        return not self.nokia_nac_token or self.nokia_nac_token == "your_nokia_nac_api_token_here"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
