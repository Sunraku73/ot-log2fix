"""Suddivisione del log su confini di riga e selezione del chunk."""

import re
from collections.abc import Callable


def split_chunks(text: str, max_chars: int, measure: Callable[[str], int] = len) -> list[str]:
    """Raggruppa righe con misura additiva: measure(a+b) == measure(a)+measure(b)."""
    if max_chars <= 0:
        raise ValueError("Il limite del chunk deve essere positivo")
    chunks: list[str] = []
    parts: list[str] = []
    size = 0
    costs: dict[str, int] = {}
    for line in text.splitlines(keepends=True):
        length = measure(line)
        if length > max_chars:
            start = 0
            accumulated = 0
            pieces: list[str] = []
            for index, char in enumerate(line):
                if char not in costs:
                    costs[char] = measure(char)
                cost = costs[char]
                if cost > max_chars:
                    raise ValueError("Un carattere supera il limite del chunk")
                if accumulated + cost > max_chars:
                    pieces.append(line[start:index])
                    start, accumulated = index, 0
                accumulated += cost
            if pieces:
                if parts:
                    chunks.append("".join(parts))
                    parts, size = [], 0
                chunks.extend(pieces)
                chunks.append(line[start:])
                continue
            length = accumulated
        if size + length > max_chars:
            chunks.append("".join(parts))
            parts, size = [], 0
        parts.append(line)
        size += length
    if parts:
        chunks.append("".join(parts))
    return chunks


def select_chunk(chunks: list[str]) -> tuple[int, str]:
    """Sceglie il chunk con più livelli ERROR/FATAL, il più recente a parità."""
    if not chunks:
        raise ValueError("Nessun chunk disponibile")

    def score(chunk: str) -> int:
        count = 0
        for line in chunk.splitlines():
            prefix = line[:80].split('"', 1)[0]
            count += len(re.findall(r"\b(?:ERROR|FATAL)\b", prefix, re.IGNORECASE))
        return count

    index = max(range(len(chunks)), key=lambda i: (score(chunks[i]), i))
    return index, chunks[index]
