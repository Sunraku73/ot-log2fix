"""Interfaccia a riga di comando di OT-Log2Fix."""

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.text import Text

from . import __version__ as package_version
from .chunker import select_chunk, split_chunks
from .config import Settings
from .prompts import load_prompt
from .providers import ProviderError, chat, create_client, is_loopback
from .redaction import redact
from .report import ReportMeta, markdown, render
from .schema import AnalysisResult

app = typer.Typer(help="Analizza log OpenText con LLM locali o cloud.", no_args_is_help=True)
console = Console()
MAX_LOG_BYTES = 10 * 1024 * 1024


@app.command()
def version() -> None:
    """Mostra la versione."""
    console.print(f"OT-Log2Fix {package_version}")


@app.command()
def analyze(
    path: str = typer.Argument(..., help="File di log da analizzare"),
    md: Path | None = None,
) -> None:
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

    def measure(value: str) -> int:
        return len(
            json.dumps(value, ensure_ascii=False)[1:-1]
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )

    try:
        budget = settings.max_chunk_chars - 2
        if budget > 0 and any(measure(line) > budget for line in log.splitlines(keepends=True)):
            console.print(
                Text("Attenzione: una riga lunga è stata divisa tra i chunk.", style="yellow")
            )
        chunks = split_chunks(log, budget, measure=measure)
        index, selected = select_chunk(chunks)
        system, user = load_prompt("analyze_v1.1")
    except ValueError as exc:
        console.print(Text(f"Errore input: {exc}", style="red"))
        raise typer.Exit(code=1) from exc
    if len(chunks) > 1:
        console.print(
            Text(
                f"Attenzione: analizzato solo il chunk {index + 1} di {len(chunks)}.",
                style="yellow",
            )
        )
    encoded_log = (
        json.dumps(selected, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    )
    correction = ""
    try:
        with create_client(settings) as client:
            for attempt in range(2):
                nonce = secrets.token_hex(16)
                while nonce in selected:
                    nonce = secrets.token_hex(16)
                prompt = user.replace("{{NONCE}}", nonce).replace("{{CHUNK_INDEX}}", str(index + 1))
                prompt = prompt.replace("{{CHUNK_TOTAL}}", str(len(chunks))).replace(
                    "{{LOG}}", encoded_log
                )
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ]
                if correction:
                    messages.append({"role": "user", "content": correction})
                response = chat(client, settings, messages)
                try:
                    result = AnalysisResult.model_validate_json(response, context={"log": selected})
                    break
                except ValidationError as exc:
                    fields = set(AnalysisResult.model_fields)
                    problems = []
                    for error in exc.errors(
                        include_input=False, include_url=False, include_context=False
                    ):
                        location = error["loc"]
                        field = location[0] if location and location[0] in fields else "schema"
                        detail = error["msg"] if error["type"] == "value_error" else error["type"]
                        problems.append(f"{field}: {detail}")
                    if attempt == 1:
                        raise ProviderError(
                            "Risposta del provider non valida dopo il secondo tentativo"
                        ) from exc
                    correction = (
                        "Risposta non valida: " + "; ".join(problems) + ". Correggi il JSON."
                    )
    except ProviderError as exc:
        console.print(Text(str(exc), style="red"))
        raise typer.Exit(code=2) from exc
    render(result, console)
    if md is not None:
        try:
            md.write_text(
                markdown(
                    result,
                    ReportMeta(
                        Path(path).name,
                        index + 1,
                        len(chunks),
                        settings.provider,
                        settings.model,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                ),
                encoding="utf-8",
            )
        except (OSError, UnicodeError) as exc:
            console.print(Text(f"Errore scrittura report: {exc}", style="red"))
            raise typer.Exit(code=1) from exc
