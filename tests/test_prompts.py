from pathlib import Path
from unittest.mock import patch

import pytest

from otlog2fix.prompts import load_prompt


def test_load_prompt() -> None:
    system, user = load_prompt("analyze_v1")
    assert "<<<OTLOG_UNTRUSTED_BEGIN" in system
    assert "{{LOG}}" in user
    assert "<!-- BEGIN" not in system


@pytest.mark.parametrize("text", ["", "<!-- BEGIN SYSTEM -->system<!-- END SYSTEM -->"])
def test_missing_prompt_markers(tmp_path: Path, text: str) -> None:
    (tmp_path / "broken.md").write_text(text, encoding="utf-8")
    with patch("otlog2fix.prompts.files", return_value=tmp_path), pytest.raises(ValueError):
        load_prompt("broken")


def test_missing_prompt() -> None:
    with pytest.raises(ValueError):
        load_prompt("no_such_prompt")
