import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API creds
    client_id: str
    client_secret: str

    # API endpoint
    base_url: str = "https://api.example.com"

    # Retry/backoff
    max_retries: int = 3
    backoff_factor: float = 1.0

    # Concurrency
    concurrency_limit: int = 10

    # Anomaly detection
    rate_threshold_per_minute: int = 100

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=os.getenv("API_CONNECTOR_ENV", ".env"),
        env_file_encoding="utf-8",
    )


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
