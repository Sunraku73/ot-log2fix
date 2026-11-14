import pytest

from otlog2fix.redaction import redact


@pytest.mark.parametrize(
    "line",
    ["bypass=enabled", "compass=north", "passport=valid", "bypass del controllo", "ticket aperto"],
)
def test_ordinary_words_are_not_redacted(line: str) -> None:
    assert redact(line) == line
