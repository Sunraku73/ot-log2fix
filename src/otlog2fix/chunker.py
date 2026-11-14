"""Suddivisione del log su confini di riga."""

import re


def split_chunks(text: str, max_chars: int) -> list[str]:
    """Raggruppa le righe e divide solo quelle oltre il limite."""
    if max_chars <= 0:
        raise ValueError("Il limite del chunk deve essere positivo")
    chunks: list[str] = []
    lines: list[str] = []
    size = 0
    for line in text.splitlines(keepends=True):
        if len(line) > max_chars:
            if lines:
                chunks.append("".join(lines))
                lines = []
                size = 0
            whole_segments = (len(line) - 1) // max_chars
            for offset in range(0, whole_segments * max_chars, max_chars):
                chunks.append(line[offset : offset + max_chars])
            line = line[whole_segments * max_chars :]
        if size + len(line) > max_chars:
            chunks.append("".join(lines))
            lines = []
            size = 0
        lines.append(line)
        size += len(line)
    if lines:
        chunks.append("".join(lines))
    return chunks


def select_chunk(chunks: list[str]) -> tuple[int, str]:
    """Seleziona l'ultimo chunk con ERROR/FATAL, oppure l'ultimo."""
    if not chunks:
        raise ValueError("Nessun chunk disponibile")
    for index in range(len(chunks) - 1, -1, -1):
        if re.search(r"\b(?:ERROR|FATAL)\b", chunks[index], re.IGNORECASE):
            return index, chunks[index]
    return len(chunks) - 1, chunks[-1]
