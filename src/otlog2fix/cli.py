"""Interfaccia a riga di comando di OT-Log2Fix."""

import json
import secrets
from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

from . import __version__ as package_version
from .config import Settings
from .prompts import load_prompt
from .providers import ProviderError, chat, create_client, is_loopback
from .redaction import redact

app = typer.Typer(help="Analizza log OpenText con LLM locali o cloud.", no_args_is_help=True)
console = Console()
MAX_LOG_BYTES = 10 * 1024 * 1024


@app.command()
def version() -> None:
    """Mostra la versione."""
    console.print(f"OT-Log2Fix {package_version}")


@app.command()
def analyze(path: str = typer.Argument(..., help="File di log da analizzare")) -> None:
    """Analizza un file di log con il provider configurato."""
    try:
        with Path(path).open("rb") as source:
            data = source.read(MAX_LOG_BYTES + 1)
        if len(data) > MAX_LOG_BYTES:
            console.print("[red]Il file supera il limite di 10 MiB.[/red]")
            raise typer.Exit(code=1)
        log = data.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        console.print(Text(f"Errore lettura file: {exc}", style="red"))
        raise typer.Exit(code=1) from exc
    if not log.strip():
        console.print("[red]Il file di log è vuoto.[/red]")
        raise typer.Exit(code=1)
    settings = Settings()
    if not settings.redact and (
        settings.provider != "ollama" or not is_loopback(settings.base_url)
    ):
        console.print(
            "[red]La redaction può essere disabilitata solo con provider locale ollama.[/red]"
        )
        raise typer.Exit(code=1)
    if settings.redact:
        log = redact(log)
    try:
        system, user = load_prompt("analyze_v1")
    except ValueError as exc:
        console.print(Text(f"Errore prompt: {exc}", style="red"))
        raise typer.Exit(code=1) from exc
    nonce = secrets.token_hex(16)
    while nonce in log:
        nonce = secrets.token_hex(16)
    encoded_log = (
        json.dumps(log, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    )
    user = user.replace("{{NONCE}}", nonce).replace("{{CHUNK_INDEX}}", "1")
    user = user.replace("{{CHUNK_TOTAL}}", "1").replace("{{LOG}}", encoded_log)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        response = chat(create_client(settings), settings, messages)
    except ProviderError as exc:
        console.print(Text(str(exc), style="red"))
        raise typer.Exit(code=2) from exc
    console.print(Text(response))
