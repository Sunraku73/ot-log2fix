import pytest

from otlog2fix.redaction import redact


@pytest.mark.parametrize(
    ("value", "kind"),
    [
        ("password=secret", "password"),
        ("pwd='first\nsecond'", "password"),
        ("token=abc", "token"),
        ("api_key=secret", "token"),
        ("https://example.test/?key=sk-abcdef123&x=1", "api_key"),
        ("Authorization: Bearer abc123", "bearer"),
        ("jdbc:postgresql://host/db?user=x&password=secret", "jdbc"),
        ("user@example.test", "email"),
    ],
)
def test_redact_secrets(value: str, kind: str) -> None:
    result = redact(value)
    assert f"[REDACTED:{kind}]" in result
    assert "secret" not in result
    assert "second" not in result
    assert "sk-abcdef123" not in result


def test_redact_empty_and_plain_text() -> None:
    assert redact("") == ""
    assert redact("normal log entry") == "normal log entry"
