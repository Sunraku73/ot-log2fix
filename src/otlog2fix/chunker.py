"""Suddivisione del log su confini di riga e selezione del chunk."""

import re
from collections.abc import Callable


def split_chunks(text: str, max_chars: int, measure: Callable[[str], int] = len) -> list[str]:
    """Raggruppa righe entro il limite misurato, dividendo quelle troppo lunghe."""
    if max_chars <= 0:
        raise ValueError("Il limite del chunk deve essere positivo")
    chunks: list[str] = []
    parts: list[str] = []
    size = 0
    for line in text.splitlines(keepends=True):
        offset = 0
        while offset < len(line):
            remaining = line[offset:]
            length = measure(remaining)
            if length > max_chars:
                if parts:
                    chunks.append("".join(parts))
                    parts, size = [], 0
                low, high = 1, len(remaining)
                best = 0
                while low <= high:
                    mid = (low + high) // 2
                    if measure(remaining[:mid]) <= max_chars:
                        best, low = mid, mid + 1
                    else:
                        high = mid - 1
                if best == 0:
                    raise ValueError("Un carattere supera il limite del chunk")
                chunks.append(remaining[:best])
                offset += best
                continue
            if size + length > max_chars:
                chunks.append("".join(parts))
                parts, size = [], 0
            parts.append(remaining)
            size += length
            break
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
