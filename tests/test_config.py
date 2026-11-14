from pathlib import Path

from dotenv import dotenv_values
from pydantic import SecretStr

from otlog2fix.config import Settings


def test_defaults_match_env_example() -> None:
    example = dotenv_values(Path(__file__).parents[1] / ".env.example")
    expected = Settings(
        _env_file=None,
        **{key.removeprefix("OTLF_").lower(): value for key, value in example.items()},
    )
    assert Settings(_env_file=None).model_dump() == expected.model_dump()


def test_api_key_is_secret() -> None:
    settings = Settings(api_key=SecretStr("sensitive-test-value"))
    assert "sensitive-test-value" not in repr(settings)
    assert settings.effective_api_key == "sensitive-test-value"
    assert Settings(api_key=SecretStr("")).effective_api_key == "local-no-key"
