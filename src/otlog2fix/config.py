"""Configurazione via env/.env (prefisso OTLF_)."""
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
model_config = SettingsConfigDict(env_prefix="OTLF_", env_file=".env", extra="ignore")
provider: str = "ollama"
base_url: str = "http://127.0.0.1:11434/v1"
model: str = "qwen2.5-coder:14b"
api_key: str = ""
max_chunk_chars: int = 12000
redact: bool = True

@property
def effective_api_key(self) -> str:
    return self.api_key or "local-no-key"
