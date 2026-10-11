"""
Central configuration for HireReady backend.
Reads from environment variables / .env, with sensible local defaults so
the app runs out of the box with zero configuration.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./hireready.db"

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    AI_PROVIDER: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "claude-sonnet-4-6"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "HireReady"
    SMTP_USE_TLS: bool = True
    SMTP_SSL: bool = False

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.AI_PROVIDER and self.AI_API_KEY)

    @property
    def email_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM_EMAIL)


settings = Settings()
