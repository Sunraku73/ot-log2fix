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
