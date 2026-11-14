import pytest

from otlog2fix.chunker import select_chunk, split_chunks


def test_chunk_boundaries_and_selection() -> None:
    chunks = split_chunks("one\nERROR x\nlast\n", 8)
    assert chunks == ["one\n", "ERROR x\n", "last\n"]
    assert select_chunk(chunks) == (1, "ERROR x\n")
    assert select_chunk(["ok", "fine"]) == (1, "fine")


def test_chunk_edges() -> None:
    assert split_chunks("", 1) == []
    assert split_chunks("1234", 4) == ["1234"]
    assert split_chunks("12345", 4) == ["1234", "5"]
    with pytest.raises(ValueError):
        split_chunks("x", 0)
    with pytest.raises(ValueError):
        select_chunk([])


def test_long_line_is_split_without_changing_content() -> None:
    text = "start\n" + "x" * 20000 + "\nend"
    chunks = split_chunks(text, 12000)
    assert "".join(chunks) == text
    assert all(len(chunk) <= 12000 for chunk in chunks)


def test_select_most_level_tokens_and_ignore_quoted_user_agent() -> None:
    chunks = [
        "2026 ERROR ORA-01652\n2026 ERROR stack trace",
        "INFO a",
        "INFO b",
        'INFO user-agent="ERROR nothing"',
    ]
    assert select_chunk(chunks) == (0, chunks[0])
    assert select_chunk(["ERROR a", "FATAL b"]) == (1, "FATAL b")
    assert select_chunk(["INFO", "INFO"]) == (1, "INFO")


def test_encoded_measure_respects_budget() -> None:
    import json

    def measure(value: str) -> int:
        return len(
            json.dumps(value, ensure_ascii=False)[1:-1]
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )

    text = "<" * 12000
    chunks = split_chunks(text, 11998, measure)
    assert "".join(chunks) == text
    assert all(measure(chunk) + 2 <= 12000 for chunk in chunks)
    with pytest.raises(ValueError):
        split_chunks("<", 5, measure)
