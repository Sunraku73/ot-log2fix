"""Suddivisione del log su confini di riga."""

import re


def split_chunks(text: str, max_chars: int) -> list[str]:
    """Restituisce chunk entro il limite, senza spezzare righe."""
    if max_chars <= 0:
        raise ValueError("Il limite del chunk deve essere positivo")
    chunks: list[str] = []
    lines: list[str] = []
    size = 0
    for line in text.splitlines(keepends=True):
        if len(line) > max_chars:
            raise ValueError("Una riga del log supera il limite del chunk")
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
