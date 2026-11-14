"""Verifica manuale del percorso redazione e chunking su log sintetici."""

import resource
import sys
import time

from rich.console import Console

from otlog2fix.chunker import encoded_length, split_chunks
from otlog2fix.redaction import redact

BUDGET = 11998


def run_case(name: str, text: str) -> None:
    """Misura il percorso completo e controlla integrità e budget."""
    started = time.perf_counter()
    redacted = redact(text)
    chunks = split_chunks(redacted, BUDGET, encoded_length)
    elapsed = time.perf_counter() - started
    assert redacted == text
    assert "".join(chunks) == text
    assert all(encoded_length(chunk) <= BUDGET for chunk in chunks)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_mib = rss / (1024 * 1024 if sys.platform == "darwin" else 1024)
    Console().print(f"{name}: {elapsed:.3f} s, RSS max {rss_mib:.1f} MiB, {len(chunks)} chunk")


def main() -> None:
    run_case("Riga unica 10 MiB", "<" * (10 * 1024 * 1024))
    mixed = "2026-11-14 INFO avvio\n" * 100 + "<" * 20000 + "\n2026-11-14 ERROR fine\n"
    run_case("Log misto", mixed)


if __name__ == "__main__":
    main()
