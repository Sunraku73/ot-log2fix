"""Gate di non divulgazione dei valori sintetici delle fixture."""

import csv
from collections import defaultdict
from pathlib import Path

import pytest

from otlog2fix.redaction import redact

FIXTURES = Path(__file__).parent / "fixtures"


def load_canaries() -> dict[str, list[tuple[str, str, str]]]:
    groups: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    definitions: dict[str, tuple[str, str, str]] = {}
    seen: set[tuple[str, str]] = set()
    with (FIXTURES / "redaction_canaries.tsv").open(encoding="utf-8", newline="") as source:
        for row in csv.reader(source, delimiter="\t"):
            if not row or row[0].startswith("#"):
                continue
            identifier, level, fixture, _vector, value = row
            assert identifier and value and level in {"MUST", "SHOULD"}
            assert (FIXTURES / fixture).is_file()
            definition = (level, fixture, _vector)
            assert identifier not in definitions or definitions[identifier] == definition
            assert (identifier, value) not in seen
            definitions[identifier] = definition
            seen.add((identifier, value))
            groups[identifier].append((level, fixture, value))
    return dict(groups)


CANARIES = load_canaries()


@pytest.mark.parametrize(
    "identifier", [key for key, rows in CANARIES.items() if rows[0][0] == "MUST"]
)
def test_must_canaries(identifier: str) -> None:
    for _level, fixture, value in CANARIES[identifier]:
        assert value not in redact((FIXTURES / fixture).read_bytes().decode("utf-8"))


@pytest.mark.xfail(reason="Copertura SHOULD non obbligatoria", strict=True)
@pytest.mark.parametrize(
    "identifier", [key for key, rows in CANARIES.items() if rows[0][0] == "SHOULD"]
)
def test_should_canaries(identifier: str) -> None:
    for _level, fixture, value in CANARIES[identifier]:
        assert value not in redact((FIXTURES / fixture).read_bytes().decode("utf-8"))


def test_canary_inventory() -> None:
    assert CANARIES
    assert all(rows for rows in CANARIES.values())
