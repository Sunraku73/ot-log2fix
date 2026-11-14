from typer.testing import CliRunner
from otlog2fix.cli import app
runner = CliRunner()
def test_version() -> None:
result = runner.invoke(app, ["version"])
assert result.exit_code == 0
assert "OT-Log2Fix" in result.stdout
