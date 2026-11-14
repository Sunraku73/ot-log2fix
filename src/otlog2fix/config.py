"""Configurazione via env/.env (prefisso OTLF_)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OTLF_", env_file=".env", extra="ignore")

    provider: str = "ollama"  # ollama | openrouter
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen3:8b"
    api_key: str = ""
    max_chunk_chars: int = 12000
    redact: bool = True

    @property
    def effective_api_key(self) -> str:
        # Ollama non richiede una key, ma l'SDK openai ne pretende una non vuota.
        return self.api_key or "local-no-key"
