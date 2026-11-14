"""Report Markdown e rendering testuale sicuro con Rich."""

import html
import re

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .schema import SENTINEL, AnalysisResult


def _escape(value: str) -> str:
    value = html.escape(" ".join(value.splitlines()), quote=False)
    return re.sub(r"([\\`*_{}\[\]()!#|~])", r"\\\1", value).replace(":", "&#58;")


def markdown(result: AnalysisResult) -> str:
    evidence = "\n".join(
        item.replace("![", r"\![").replace("](", r"]\(") for item in result.evidence
    )
    fence = "`" * max(3, max((len(m.group()) for m in re.finditer(r"`+", evidence)), default=0) + 1)
    lines = [
        "# Analisi del log",
        "",
        f"**Stato:** {_escape(result.status)}",
        f"**Confidenza:** {_escape(result.confidence)}",
        "",
        "## Causa",
        _escape(result.root_cause),
        "",
        "## Evidenze",
        f"{fence}text",
        evidence,
        fence,
        "",
        "## Azioni",
    ]
    lines.extend(f"{i}. {_escape(step)}" for i, step in enumerate(result.fix_steps, 1))
    lines.extend(["", "## Contesto mancante"])
    lines.extend(f"- {_escape(item)}" for item in result.missing_context)
    lines.extend(
        [
            "",
            f"**Injection rilevata:** {'sì' if result.injection_detected else 'no'}",
            "",
            "## Note",
            _escape(result.notes),
            "",
        ]
    )
    return "\n".join(lines)


def render(result: AnalysisResult, console: Console) -> None:
    console.print(Text("Analisi del log", style="bold"))
    if result.root_cause == SENTINEL:
        console.print(Panel(Text(SENTINEL), border_style="yellow"))
    else:
        console.print(Text(f"Causa: {result.root_cause}"))
    console.print(Text(f"Stato: {result.status} | Confidenza: {result.confidence}"))
    console.print(Text("Evidenze:", style="bold"))
    for item in result.evidence:
        console.print(Text(item))
    console.print(Text("Azioni:", style="bold"))
    for index, step in enumerate(result.fix_steps, 1):
        console.print(Text(f"{index}. {step}"))
    for item in result.missing_context:
        console.print(Text(f"Contesto mancante: {item}"))
    console.print(Text(f"Injection rilevata: {'sì' if result.injection_detected else 'no'}"))
    if result.notes:
        console.print(Text(f"Note: {result.notes}"))
