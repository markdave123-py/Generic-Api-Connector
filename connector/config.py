import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from connector.secret_provider import EnvProvider, FileProvider, SecretProvider


class Settings(BaseSettings):
    # ────────── CROSS-CONNECTOR FIELDS ──────────────────────────────
    provider: str = "default"  # e.g. sim / google / twitter
    secret_backend: str = os.getenv("SECRET_BACKEND", "docker")  # env | docker

    # secret names are built as  <provider>_<suffix>
    client_id_suffix: str = "client_id"
    client_secret_suffix: str = "client_secret"

    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    base_url: str = "https://api.example.com"
    max_retries: int = 3
    backoff_factor: float = 1.0
    concurrency_limit: int = 10
    rate_threshold_per_minute: int = 100

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=os.getenv("API_CONNECTOR_ENV", ".env"),
        env_file_encoding="utf-8",
    )

    def _provider_backend(self) -> SecretProvider:
        return FileProvider() if self.secret_backend == "docker" else EnvProvider()

    def _secret_name(self, suffix: str) -> str:
        return f"{self.provider}_{suffix}"

    async def client_id_async(self) -> str:
        if self.client_id:  # env-var path (dev/CI)
            return self.client_id
        return await self._provider_backend().get(
            self._secret_name(self.client_id_suffix)
        )

    async def client_secret_async(self) -> str:
        if self.client_secret:
            return self.client_secret
        return await self._provider_backend().get(
            self._secret_name(self.client_secret_suffix)
        )


def get_settings() -> Settings:
    return Settings()  # cached by Pydantic
