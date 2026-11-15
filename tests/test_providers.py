from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import openai
import pytest

from otlog2fix.config import Settings
from otlog2fix.providers import ProviderError, chat, create_client


def status_error(status: int) -> openai.APIStatusError:
    response = MagicMock()
    response.status_code = status
    return openai.APIStatusError("error", response=response, body=None)


def test_create_client() -> None:
    with patch("otlog2fix.providers.OpenAI") as constructor:
        settings = Settings(base_url="https://example.test/v1", api_key="test-key")
        assert create_client(settings) is constructor.return_value
        constructor.assert_called_once_with(
            base_url=settings.base_url, api_key="test-key", timeout=300.0, max_retries=0
        )


def test_create_client_local_key() -> None:
    with patch("otlog2fix.providers.OpenAI") as constructor:
        create_client(Settings(api_key=""))
        assert constructor.call_args.kwargs["api_key"] == "local-no-key"


def test_chat_retries_then_succeeds() -> None:
    client = MagicMock()
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])
    client.chat.completions.create.side_effect = [status_error(429), status_error(503), reply]
    with patch("otlog2fix.providers.time.sleep") as sleep:
        assert chat(client, Settings(), [{"role": "user", "content": "log"}]) == "ok"
    assert client.chat.completions.create.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2]
    assert client.chat.completions.create.call_args.kwargs["timeout"] == 300.0


@pytest.mark.parametrize("status, calls", [(400, 1), (500, 3)])
def test_chat_status_failure(status: int, calls: int) -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = status_error(status)
    with patch("otlog2fix.providers.time.sleep"), pytest.raises(ProviderError):
        chat(client, Settings(), [])
    assert client.chat.completions.create.call_count == calls


def test_chat_invalid_response() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value.choices = []
    with pytest.raises(ProviderError):
        chat(client, Settings(), [])


def test_create_client_invalid_configuration() -> None:
    with (
        patch("otlog2fix.providers.OpenAI", side_effect=ValueError("invalid")),
        pytest.raises(ProviderError),
    ):
        create_client(Settings())


def test_chat_connection_error() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = openai.APIConnectionError(request=MagicMock())
    settings = Settings(base_url="http://user:secret@localhost:11434/v1?token=hidden")
    with pytest.raises(ProviderError) as error:
        chat(client, settings, [])
    assert str(error.value) == (
        "Provider non raggiungibile su http://localhost:11434. Verifica che Ollama sia attivo."
    )
    assert "secret" not in str(error.value) and "hidden" not in str(error.value)


def test_chat_timeout_error() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = openai.APITimeoutError(request=MagicMock())
    with pytest.raises(ProviderError, match="Timeout del provider dopo 10s.*OTLF_TIMEOUT"):
        chat(client, Settings(timeout=10), [])


def test_chat_404_hides_response_body() -> None:
    client = MagicMock()
    error = status_error(404)
    error.body = "secret response body"
    client.chat.completions.create.side_effect = error
    with pytest.raises(ProviderError) as result:
        chat(client, Settings(model="example-model"), [])
    assert str(result.value) == (
        "Errore provider HTTP 404. Modello non trovato. Esegui: ollama pull example-model"
    )


def test_chat_other_http_error() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = status_error(403)
    with pytest.raises(ProviderError, match="^Errore provider HTTP 403$"):
        chat(client, Settings(), [])


def test_local_client_ignores_proxy_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(variable, "http://proxy.example.test:8080")
    client = create_client(Settings(base_url="http://localhost:11434/v1"))
    try:
        assert client._client.trust_env is False
    finally:
        client.close()


def test_cloud_client_keeps_default_proxy_behavior() -> None:
    with patch("otlog2fix.providers.OpenAI") as constructor:
        create_client(Settings(base_url="https://example.test/v1"))
        assert "http_client" not in constructor.call_args.kwargs
