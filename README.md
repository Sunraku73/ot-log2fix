# OT-Log2Fix

CLI che analizza log OpenText (Content Server, AppWorks) con LLM locali (Ollama)
o cloud (OpenRouter) e produce un report Markdown: root cause + fix suggeriti.

> Stato: pre-alpha. Vedi [docs/PLAN.md](docs/PLAN.md) per la roadmap.

## Quickstart

    python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
    cp .env.example .env
    .venv/bin/otlog2fix version

## Privacy
Redaction di password/token/PII prima di qualsiasi chiamata al modello.
Modalita' 100% locale con Ollama per ambienti air-gapped.

## Licenza
MIT
