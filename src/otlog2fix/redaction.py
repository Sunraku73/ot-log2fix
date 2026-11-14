"""Rimozione di dati sensibili preservando le righe originali innocue."""

import html
import re
import unicodedata
from urllib.parse import unquote

_FLAGS = re.IGNORECASE
_PASSWORD = r"(?:password|passwd|pwd|pass|secret|\\u0070assword)"
_VALUE = r"""(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s&;,]+)"""
_VALUE_PATTERN = re.compile(_VALUE)

# Riconosce nomi completi, inclusi prefissi e suffissi separati o camelCase.
_ASSIGNMENT = re.compile(
    r"""(?<![\w-])(?P<key>[\w\\-]+)["']?[ \t]*[=:][ \t]*""",
    _FLAGS,
)
_SPECIAL_TICKET = re.compile(r"\b(?:otcsticket|otdsticket|llcookie)[ \t]+[^\s;,]+", _FLAGS)
_PATTERNS = (
    ("jdbc", re.compile(r"jdbc:[^\s\"'<>]+", _FLAGS)),
    ("url_credentials", re.compile(r"(?<![\w+.-])(?:[a-z][\w+.-]*:)?//[^\s/]*@", _FLAGS)),
    ("sql_credentials", re.compile(r"""\b[\w.-]+/(?:"[^"]*"|'[^']*'|[^\s@]+)@[^\s]+""", _FLAGS)),
    ("bearer", re.compile(r"\bBearer[ \t]+[^\s\"'<>]+", _FLAGS)),
    ("basic", re.compile(r"\bBasic[ \t]+[A-Za-z0-9+/=]+", _FLAGS)),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9_-]+", _FLAGS)),
    ("token", _SPECIAL_TICKET),
    ("password", re.compile(rf"""\b{_PASSWORD}[ \t]+(?:"[^"]*"|'[^']*')""", _FLAGS)),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", _FLAGS)),
    (
        "email",
        re.compile(
            r"\b[A-Z0-9._%+-]+[ \t]*\[at\][ \t]*[A-Z0-9.-]+[ \t]*\[dot\][ \t]*[A-Z0-9.-]+", _FLAGS
        ),
    ),
)
_KEY_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|[_-]+")
_PEM_TYPES = frozenset(
    {
        "PRIVATE KEY",
        "RSA PRIVATE KEY",
        "EC PRIVATE KEY",
        "ENCRYPTED PRIVATE KEY",
        "OPENSSH PRIVATE KEY",
        "PGP PRIVATE KEY BLOCK",
    }
)


def _key_kind(key: str) -> str | None:
    parts = [part.lower() for part in _KEY_SPLIT.split(key)]
    lowered = key.lower()
    if (
        any(part in {"password", "passwd", "pwd", "pass", "secret"} for part in parts)
        or lowered == r"\u0070assword"
    ):
        return "password"
    if any(
        part in {"token", "ticket", "otcsticket", "otdsticket", "llcookie"} for part in parts
    ) or lowered in {"apikey", "api_key", "api-key"}:
        return "token"
    return None


def _apply_patterns(text: str) -> str:
    for kind, pattern in _PATTERNS:
        text = pattern.sub(f"[REDACTED:{kind}]", text)

    pieces: list[str] = []
    position = 0
    for match in _ASSIGNMENT.finditer(text):
        if match.start() < position:
            continue
        kind = _key_kind(match.group("key"))
        value = _VALUE_PATTERN.match(text, match.end()) if kind else None
        if value:
            pieces.append(text[position : match.start()])
            pieces.append(f"[REDACTED:{kind}]")
            position = value.end()
    pieces.append(text[position:])
    return "".join(pieces)


def _pem_header(text: str, position: int, marker: str) -> tuple[str, int] | None:
    # L'unwrapping è limitato al riconoscimento dell'header, non altera il log.
    window = text[position : position + 80]
    end = window.find("-----", len(marker))
    if end < 0:
        return None
    header = window[len(marker) : end].replace("\n", "").replace("\r", "")
    if header not in _PEM_TYPES:
        return None
    return header, position + end + 5


def _redact_private_keys(text: str) -> str:
    parts: list[str] = []
    position = 0
    while (start := text.find("-----BEGIN ", position)) >= 0:
        header = _pem_header(text, start, "-----BEGIN ")
        if header is None:
            parts.append(text[position : start + 11])
            position = start + 11
            continue
        kind, body = header
        parts.extend((text[position:start], "[REDACTED:private_key]"))
        end = text.find(f"-----END {kind}-----", body)
        if end < 0:
            return "".join(parts)
        position = end + len(f"-----END {kind}-----")
    parts.append(text[position:])
    return "".join(parts)


_YAML_BLOCK = re.compile(
    rf"""(?<![a-zA-Z0-9]){_PASSWORD}["']?[ \t]*:[ \t]*[|>][-+]?[ \t]*$""", _FLAGS
)
_XML_PASSWORD = re.compile(rf"<({_PASSWORD})\b[^>]*>[^<]*</\1\s*>", _FLAGS)
_MULTILINE_VALUE = re.compile(
    rf"""(?<![\w]){_PASSWORD}["']?[ \t]*[=:][ \t]*\r?\n[ \t]*{_VALUE}""", _FLAGS
)
_QUOTED_MULTILINE = re.compile(
    rf"""(?<![\w]){_PASSWORD}["']?[ \t]*[=:][ \t]*(?:"[^"\r\n]*\r?\n[^"]*"|'[^'\r\n]*\r?\n[^']*')""",
    _FLAGS,
)
_CONTINUED_PASSWORD = re.compile(
    rf"""(?<![\w]){_PASSWORD}[ \t]*=[ \t]*[^\s\\]+\\\r?\n[ \t]*[^\s&;,]+""", _FLAGS
)
_CONFIG_START = re.compile(
    r"\b[\w.-]*(?:config|credential)[\w.-]*_b64[ \t]*=[ \t]*[A-Za-z0-9+/=]+[ \t]*$", _FLAGS
)
_BASE64_LINE = re.compile(r"[ \t]*[A-Za-z0-9+/=]+[ \t]*$")


def _redact_multiline(text: str) -> str:
    text = _redact_private_keys(text)
    for pattern in (_XML_PASSWORD, _QUOTED_MULTILINE, _CONTINUED_PASSWORD, _MULTILINE_VALUE):
        text = pattern.sub("[REDACTED:password]", text)
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        content = line.rstrip("\r\n")
        yaml = _YAML_BLOCK.search(content)
        config = _CONFIG_START.search(content)
        match = yaml or config
        if not match:
            output.append(line)
            index += 1
            continue
        output.append(
            line[: match.start()]
            + ("[REDACTED:password]" if yaml else "[REDACTED:config]")
            + line[len(content) :]
        )
        index += 1
        while index < len(lines):
            next_line = lines[index]
            if (
                yaml
                and (next_line.startswith((" ", "\t")) or not next_line.strip())
                or config
                and _BASE64_LINE.fullmatch(next_line.rstrip("\r\n"))
            ):
                index += 1
            else:
                break
    return "".join(output)


def _normalize(line: str) -> tuple[str, bool]:
    normalized = line
    if "%" in line or "&" in line:
        for _ in range(10):
            updated = html.unescape(unquote(normalized))
            if updated == normalized:
                break
            normalized = updated
        else:
            if html.unescape(unquote(normalized)) != normalized:
                return normalized, False
    normalized = normalized.replace(r"\/", "/")
    normalized = re.sub(r"[\u200b-\u200d\u2060\ufeff]", "", normalized)
    return unicodedata.normalize("NFKC", normalized), True


def redact(text: str) -> str:
    """Redige blocchi originali e poi singole righe, senza crearne di nuove."""
    result: list[str] = []
    for whole_line in _redact_multiline(text).splitlines(keepends=True):
        line = whole_line.rstrip("\r\n")
        ending = whole_line[len(line) :]
        normalized, stable = _normalize(line)
        if not stable:
            result.append("[REDACTED:opaque_line]" + ending)
            continue
        redacted = _apply_patterns(normalized)
        if redacted != normalized:
            result.append(re.sub(r"[\r\n\v\f\x1c-\x1e\x85\u2028\u2029]", "⏎", redacted) + ending)
        else:
            result.append(_apply_patterns(line) + ending)
    return "".join(result)
