"""Configurazione via env/.env (prefisso OTLF_)."""

import codecs

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OTLF_", env_file=".env", extra="ignore")
    provider: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen3:8b"
    api_key: SecretStr = SecretStr("")
    max_chunk_chars: int = Field(default=12000, ge=1000)
    redact: bool = True
    timeout: float = Field(default=300.0, ge=10, le=3600)
    encoding: str = "utf-8"

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, value: str) -> str:
        try:
            codecs.lookup(value)
        except LookupError as exc:
            raise ValueError("Encoding non valido") from exc
        return value

    @property
    def effective_api_key(self) -> str:
        return self.api_key.get_secret_value() or "local-no-key"
