"""Accesso ai provider OpenAI-compatible."""

import time
from typing import Any
from urllib.parse import urlsplit

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    DefaultHttpxClient,
    OpenAI,
    OpenAIError,
)

from .config import Settings


class ProviderError(Exception):
    """Errore durante la comunicazione con il provider."""


def is_loopback(base_url: str) -> bool:
    """Determina la località dal solo host della URL configurata."""
    try:
        return urlsplit(base_url).hostname in {"localhost", "127.0.0.1", "::1"}
    except ValueError:
        return False


def create_client(settings: Settings) -> OpenAI:
    """Crea il client con retry gestiti esplicitamente da chat."""
    try:
        kwargs: dict[str, Any] = {}
        if is_loopback(settings.base_url):
            kwargs["http_client"] = DefaultHttpxClient(trust_env=False)
        return OpenAI(
            base_url=settings.base_url,
            api_key=settings.effective_api_key,
            timeout=settings.timeout,
            max_retries=0,
            **kwargs,
        )
    except (OpenAIError, ValueError) as exc:
        raise ProviderError("Configurazione del provider non valida") from exc


def chat(client: OpenAI, settings: Settings, messages: list[dict[str, str]]) -> str:
    """Invia messaggi, ritentando fino a due volte per HTTP 429 e 5xx."""
    for attempt in range(3):
        try:
            response: Any = client.chat.completions.create(
                model=settings.model, messages=messages, timeout=settings.timeout
            )
            content = response.choices[0].message.content
            if not isinstance(content, str):
                raise ProviderError("Risposta del provider priva di contenuto testuale")
            return content
        except APIStatusError as exc:
            if (exc.status_code == 429 or exc.status_code >= 500) and attempt < 2:
                time.sleep(2**attempt)
                continue
            message = f"Errore provider HTTP {exc.status_code}"
            if exc.status_code == 404:
                message += f". Modello non trovato. Esegui: ollama pull {settings.model}"
            raise ProviderError(message) from exc
        except APITimeoutError as exc:
            raise ProviderError(
                f"Timeout del provider dopo {settings.timeout:g}s. "
                "Su CPU aumenta OTLF_TIMEOUT (es. 600)."
            ) from exc
        except APIConnectionError as exc:
            try:
                url = urlsplit(settings.base_url)
                host = url.hostname
                if url.scheme not in {"http", "https"} or not host:
                    raise ValueError("URL non valida")
                host = f"[{host}]" if ":" in host else host
                port = url.port or (443 if url.scheme == "https" else 80)
                endpoint = f"{url.scheme}://{host}:{port}"
            except ValueError:
                endpoint = "endpoint non valido"
            raise ProviderError(
                f"Provider non raggiungibile su {endpoint}. Verifica che Ollama sia attivo."
            ) from exc
        except APIError as exc:
            raise ProviderError("Errore di comunicazione con il provider") from exc
        except (IndexError, AttributeError, TypeError) as exc:
            raise ProviderError("Risposta del provider non valida") from exc
    raise ProviderError("Errore del provider")
