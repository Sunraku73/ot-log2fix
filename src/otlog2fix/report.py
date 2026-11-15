"""Report Markdown e rendering testuale sicuro con Rich."""

import html
import re
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .schema import SENTINEL, AnalysisResult


@dataclass(frozen=True)
class ReportMeta:
    filename: str
    chunk_index: int
    chunk_total: int
    provider: str
    model: str
    timestamp_utc: str
    fallback: bool = False


def _safe(value: str) -> str:
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "\ufffd", value)


def _escape(value: str) -> str:
    value = html.escape(" ".join(_safe(value).splitlines()), quote=False)
    value = re.sub(r"([\\`*_{}\[\]()!#|~])", r"\\\1", value)
    value = re.sub(r"(?i)www\.", "www&#46;", value).replace("@", "&#64;<!-- -->")
    return re.sub(
        r"(?i)\b([a-z][a-z0-9+.-]*)(:)(?=//)|\b(javascript|data|mailto)(:)",
        lambda m: (m.group(1) or m.group(3)) + "&#58;",
        value,
    )


def markdown(result: AnalysisResult, meta: ReportMeta) -> str:
    evidence = "\n".join(_safe(item) for item in result.evidence)
    injection = "non valutata" if meta.fallback else "sì" if result.injection_detected else "no"
    fence = "`" * max(3, max((len(m.group()) for m in re.finditer(r"`+", evidence)), default=0) + 1)
    lines = [
        *(["**Report di fallback — analisi non completata**", ""] if meta.fallback else []),
        "# Analisi del log",
        "",
        *(
            [f"**Analisi parziale: chunk {meta.chunk_index} di {meta.chunk_total}**", ""]
            if meta.chunk_total > 1
            else []
        ),
        f"**File:** {_escape(meta.filename)}",
        f"**Chunk:** {meta.chunk_index} di {meta.chunk_total}",
        f"**Provider:** {_escape(meta.provider)} · **Modello:** {_escape(meta.model)}",
        f"**Timestamp UTC:** {_escape(meta.timestamp_utc)}",
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
            f"**Injection rilevata:** {injection}",
            "",
            "## Note",
            _escape(result.notes),
            "",
        ]
    )
    return "\n".join(lines)


def render(result: AnalysisResult, console: Console, *, fallback: bool = False) -> None:
    if fallback:
        console.print(
            Panel(
                Text(
                    "Report di fallback: il modello non ha prodotto una risposta valida. "
                    "Nessuna analisi del contenuto è completata."
                ),
                border_style="yellow",
            )
        )
    console.print(Text("Analisi del log", style="bold"))
    if result.root_cause == SENTINEL:
        console.print(Panel(Text(SENTINEL), border_style="yellow"))
    else:
        console.print(Text(f"Causa: {_safe(result.root_cause)}"))
    console.print(Text(f"Stato: {_safe(result.status)} | Confidenza: {_safe(result.confidence)}"))
    console.print(Text("Evidenze:", style="bold"))
    for item in result.evidence:
        console.print(Text(_safe(item)))
    console.print(Text("Azioni:", style="bold"))
    for index, step in enumerate(result.fix_steps, 1):
        console.print(Text(f"{index}. {_safe(step)}"))
    for item in result.missing_context:
        console.print(Text(f"Contesto mancante: {_safe(item)}"))
    injection = "non valutata" if fallback else "sì" if result.injection_detected else "no"
    console.print(Text(f"Injection rilevata: {injection}"))
    if result.notes:
        console.print(Text(f"Note: {_safe(result.notes)}"))
