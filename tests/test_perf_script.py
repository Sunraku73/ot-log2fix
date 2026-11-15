import builtins
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.parametrize("without_resource", [False, True])
def test_perf_script_with_and_without_resource(
    without_resource: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    original_import = builtins.__import__

    def import_module(name: str, *args: object, **kwargs: object) -> object:
        if name == "resource" and without_resource:
            raise ImportError("resource unavailable")
        return original_import(name, *args, **kwargs)

    script = Path(__file__).parents[1] / "scripts" / "perf_chunker.py"
    with patch("builtins.__import__", side_effect=import_module):
        module = runpy.run_path(str(script))
    module["run_case"]("synthetic", "safe text")
    output = capsys.readouterr().out
    assert "synthetic:" in output and "1 chunk" in output
    assert ("RSS max" in output) == (module["resource"] is not None)
    if without_resource:
        assert module["resource"] is None
