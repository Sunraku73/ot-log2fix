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
            base_url=settings.base_url, api_key="test-key", timeout=60.0, max_retries=0
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
    assert client.chat.completions.create.call_args.kwargs["timeout"] == 60.0


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
    with patch("otlog2fix.providers.OpenAI", side_effect=ValueError("invalid")), pytest.raises(
        ProviderError
    ):
        create_client(Settings())


def test_chat_connection_error() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = openai.APIConnectionError(request=MagicMock())
    with pytest.raises(ProviderError):
        chat(client, Settings(), [])
