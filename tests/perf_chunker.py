"""Verifica separata in CI delle prestazioni su una riga sintetica da 10 MiB."""

from rich.console import Console

from otlog2fix.chunker import encoded_length, split_chunks


def main() -> None:
    text = "<" * (10 * 1024 * 1024)
    chunks = split_chunks(text, 11998, encoded_length)
    assert "".join(chunks) == text
    assert all(encoded_length(chunk) <= 11998 for chunk in chunks)
    Console().print(f"10 MiB: {len(chunks)} chunk verificati")


if __name__ == "__main__":
    main()
