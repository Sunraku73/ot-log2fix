from typer.testing import CliRunner

from otlog2fix.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "OT-Log2Fix 0.1.0" in result.stdout
