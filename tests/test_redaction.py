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


def test_multiline_password_continuation_preserves_next_record() -> None:
    result = redact("password=first\\\n  second\nnormal entry")
    assert "first" not in result
    assert "second" not in result
    assert "normal entry" in result


def test_encoded_query_key_does_not_remove_other_parameters() -> None:
    result = redact("https://example.test/?p%61ssword=secret&safe=value")
    assert "secret" not in result
    assert "safe=value" in result


def test_normalization_returns_redacted_normalized_text() -> None:
    result = redact("ＦＯＯ %2570ass&#119;ord=secret pass\u200bword=hidden https:\\/\\/x")
    assert "FOO" in result
    assert "secret" not in result
    assert "hidden" not in result
    assert "https://x" in result


def test_redaction_long_adversarial_line_finishes() -> None:
    import subprocess
    import sys

    code = (
        "from otlog2fix.redaction import redact; "
        "redact('<password>' * (1048576 // len('<password>')))"
    )
    subprocess.run([sys.executable, "-c", code], timeout=5, check=True)


def test_multiline_yaml_and_unterminated_private_key() -> None:
    result = redact("password: |\n  first\n  second\nnext=ok\n")
    assert "first" not in result and "second" not in result
    assert "next=ok" in result
    assert "secret-value" not in redact("-----BEGIN PRIVATE KEY-----\nsecret-value")


def test_encoded_newline_cannot_forge_lines() -> None:
    clean = "line1 %0A2026-11-14 ERROR forged"
    assert redact(clean) == clean
    result = redact("password=x%0AERROR forged")
    assert "x" not in result
    assert "⏎ERROR forged" in result
    assert len(result.splitlines()) == 1


def test_crlf_and_original_clean_line_preserved() -> None:
    source = "raw %41 &amp; Ａ\r\npassword=value\r\nplain\n"
    result = redact(source)
    assert result == "raw %41 &amp; Ａ\r\n[REDACTED:password]\r\nplain\n"


def test_decoding_limit_is_fail_closed() -> None:
    encoded = "%" + "25" * 11 + "41"
    assert redact(f"opaque={encoded}\r\n") == "[REDACTED:opaque_line]\r\n"


@pytest.mark.parametrize(
    "kind",
    [
        "PRIVATE KEY",
        "RSA PRIVATE KEY",
        "EC PRIVATE KEY",
        "ENCRYPTED PRIVATE KEY",
        "OPENSSH PRIVATE KEY",
        "PGP PRIVATE KEY BLOCK",
    ],
)
def test_pem_wrapped_and_unterminated(kind: str) -> None:
    wrapped = kind[:3] + "\n" + kind[3:]
    source = f"before -----BEGIN {wrapped}-----\nsecretbody\n-----END {kind}----- after"
    assert redact(source) == "before [REDACTED:private_key] after"
    assert (
        redact(f"before -----BEGIN {wrapped}-----\nsecretbody") == "before [REDACTED:private_key]"
    )


def test_decoded_unicode_line_separator_does_not_create_record() -> None:
    result = redact("password=x&#8232;forged")
    assert len(result.splitlines()) == 1
    assert "⏎forged" in result
