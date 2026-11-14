"""Rimozione di dati sensibili dai log prima dell'invio."""

import re

# Le stringhe JDBC vengono elaborate per prime, perché possono includere altri segreti.
_PATTERNS = (
    ("jdbc", re.compile(r"jdbc:[^\s\"'<>]+", re.IGNORECASE)),
    ("bearer", re.compile(r"\bBearer\s+[^\s\"'<>]+", re.IGNORECASE)),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9_-]+", re.IGNORECASE)),
    (
        "password",
        re.compile(
            r"\b(?:password|pwd)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s&;,]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "token",
        re.compile(
            r"\b(?:token|api[_-]?key)\s*[=:]\s*(?:\"[^\"]*\"|'[^']*'|[^\s&;,]+)",
            re.IGNORECASE,
        ),
    ),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
)


def redact(text: str) -> str:
    """Sostituisce i segreti riconosciuti con segnaposto tipizzati."""
    for kind, pattern in _PATTERNS:
        text = pattern.sub(f"[REDACTED:{kind}]", text)
    return text
