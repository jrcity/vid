"""
app/core/config.py
Central configuration — reads from .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import model_validator
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
    use_simulator: bool = True

    # CORS — comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:3000,https://panafricanvid.vercel.app"

    # Optional: Anthropic for AI explainer  
    anthropic_api_key: str = ""

    # Certificate verification store
    certificate_store_path: str = "data/certificates.db"

    # Public URL used inside generated QR codes
    verify_base_url: str = "https://panafricanvid.vercel.app/verify"

    # Basic API abuse protection
    rate_limit_default: str = "120/minute"
    rate_limit_enroll: str = "20/minute"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

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

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.is_production:
            if self.secret_key in {"change_me_in_production", "change_this_to_a_random_64_char_string"}:
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.cors_origins_list:
                raise ValueError("CORS_ORIGINS must include at least one production frontend origin")
            if "*" in self.cors_origins_list:
                raise ValueError("CORS_ORIGINS cannot include '*' in production")
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
