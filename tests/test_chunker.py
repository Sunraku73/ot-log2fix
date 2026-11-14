import pytest

from otlog2fix.chunker import encoded_length, select_chunk, split_chunks


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
    text = "<" * 12000
    chunks = split_chunks(text, 11998, encoded_length)
    assert "".join(chunks) == text
    assert all(encoded_length(chunk) + 2 <= 12000 for chunk in chunks)
    with pytest.raises(ValueError):
        split_chunks("<", 5, encoded_length)


def test_json_measure_is_additive() -> None:
    assert encoded_length("") == 0
    assert encoded_length("<") == 6
    samples = ["ascii", "<", ">", '"', "\\", "\n", "è漢😀"]
    for left in samples:
        for right in samples:
            assert encoded_length(left + right) == encoded_length(left) + encoded_length(right)


def test_two_megabyte_line_completes_within_budget() -> None:
    import subprocess
    import sys

    code = r"""from otlog2fix.chunker import encoded_length, split_chunks
text = "<" * (2 * 1024 * 1024)
chunks = split_chunks(text, 11998, encoded_length)
assert "".join(chunks) == text
assert all(encoded_length(chunk) <= 11998 for chunk in chunks)
"""
    subprocess.run([sys.executable, "-c", code], timeout=5, check=True)


def test_fast_path_measures_each_line_once() -> None:
    measured: list[str] = []

    def measure(value: str) -> int:
        measured.append(value)
        return len(value)

    assert split_chunks("one\ntwo\n", 5, measure) == ["one\n", "two\n"]
    assert measured == ["one\n", "two\n"]
