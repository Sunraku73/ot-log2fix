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


@pytest.mark.parametrize("separator", ["%26", "%3B", "%20", "%2526"])
def test_encoded_query_values_are_fully_redacted(separator: str) -> None:
    source = f"/login?password=Synth{separator}CANARY41&safe=b"
    result = redact(source)
    assert "Synth" not in result and "CANARY41" not in result
    assert "safe=b" in result


def test_literal_query_separator_preserves_other_parameters() -> None:
    result = redact("password=a&safe=b")
    assert "password=a" not in result
    assert "safe=b" in result


def test_unicode_escape_normalization_preserves_line_integrity() -> None:
    source = r'body={"p\u0061ssword":"test\u000aERROR"}'
    result = redact(source)
    assert "test" not in result
    assert len(result.splitlines()) == 1
    assert redact(r"clean=\u0041") == r"clean=\u0041"


def test_multiline_basic_and_xml_cdata() -> None:
    result = redact("Authorization: Basic QUJD\r\n  REVGRw==\r\n  SEk=\r\nnext line\r\n")
    assert "QUJD" not in result and "REVGRw==" not in result and "SEk=" not in result
    assert "next line" in result
    assert "CDATA-secret" not in redact("<password><![CDATA[CDATA-secret]]></password>")
    assert "CDATA-secret" not in redact("<password><![CDATA[CDATA-secret")


def test_connection_string_password_including_spaces() -> None:
    result = redact("Server=host;Password=foo bar;Database=app")
    assert "foo" not in result and "bar" not in result
    assert "Database=app" in result


@pytest.mark.parametrize("key", ["pass_count", "ticket_count", "password_length", "tokenSize"])
def test_integer_counts_are_preserved(key: str) -> None:
    line = f"{key}=123"
    assert redact(line) == line


@pytest.mark.parametrize("line", ["ticket_id=SynthTkt-123", "password_count=12x", "pass_count=3.5"])
def test_non_integer_and_id_values_are_redacted(line: str) -> None:
    assert line not in redact(line)
