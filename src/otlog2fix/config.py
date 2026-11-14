"""Configurazione via env/.env (prefisso OTLF_)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OTLF_", env_file=".env", extra="ignore")
    provider: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen3:8b"
    api_key: SecretStr = SecretStr("")
    max_chunk_chars: int = 12000
    redact: bool = True

    @property
    def effective_api_key(self) -> str:
        return self.api_key.get_secret_value() or "local-no-key"
