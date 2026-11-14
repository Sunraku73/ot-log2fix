"""Caricamento dei prompt inclusi nel package."""

from importlib.resources import files


def load_prompt(name: str) -> tuple[str, str]:
    """Carica esclusivamente le sezioni SYSTEM e USER di un prompt."""
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError("Nome prompt non valido")
    try:
        template = files(__package__).joinpath(f"{name}.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("Prompt non disponibile") from exc
    sections = []
    for section in ("SYSTEM", "USER"):
        begin, end = f"<!-- BEGIN {section} -->", f"<!-- END {section} -->"
        if template.count(begin) != 1 or template.count(end) != 1:
            raise ValueError(f"Marker {section} mancanti o duplicati")
        start = template.index(begin) + len(begin)
        finish = template.index(end)
        if finish <= start or not template[start:finish].strip():
            raise ValueError(f"Sezione {section} non valida")
        sections.append(template[start:finish].strip())
    return sections[0], sections[1]
