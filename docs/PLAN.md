# Piano di sviluppo OT-Log2Fix

Planner: Qwen. Implementer: Codex (codex.md). Reviewer/Prompt engineer: Claude (claude.md).
Loop: Qwen assegna prompt -> Codex implementa -> Claude review -> Qwen decide il passo successivo.

| Sprint | Settimane | Deliverable | DoD |
|---|---|---|---|
| S1 | 1-2 | config, providers (Ollama+OpenRouter), redaction v1, CLI analyze base | make check verde, test offline |
| S2 | 3-4 | chunker, system prompt v1, report Markdown, golden tests su fixture | accuratezza su 5 fixture note |
| S3 | 5-6 | models discovery (--free), cost guard, streaming, UX, docs | costo stimato prima della call |
| S4 | 7-8 | packaging (pipx + binary), CI GitHub Actions, release v0.1.0, demo GIF | release scaricabile e testata |

## Pubblicazione e sponsorizzazione (S4)
- GitHub: topics opentext / logs / llm / cli, README con GIF demo, GitHub Sponsors + Buy Me a Coffee.
- Lancio: LinkedIn (post tecnico con caso reale anonimizzato), community OpenText (forum/LinkedIn groups), Reddit r/devops e r/LocalLLaMA.
- Footer CLI non invasivo con link sponsor (disattivabile con --no-banner).
