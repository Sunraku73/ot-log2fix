"""OT-Log2Fix CLI — skeleton di bootstrap."""
import typer
from rich.console import Console

from . import __version__

app = typer.Typer(help="Analizza log OpenText con LLM locali o cloud.", no_args_is_help=True)
console = Console()


@app.command()
def version() -> None:
    """Mostra la versione."""
    console.print(f"OT-Log2Fix {__version__}")


@app.command()
def analyze(path: str = typer.Argument(..., help="File di log da analizzare")) -> None:
    """[Sprint 1] Analisi del log — implementazione assegnata a Codex."""
    console.print(f"[yellow]TODO Sprint 1:[/yellow] analisi di {path}")
