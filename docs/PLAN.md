# Piano

Owner del file: Claude (da S1.6). Un task si spunta solo dopo il verdetto APPROVED della review.

## Sprint 1 — chiuso (2026-11-14)

- [x] S1.1 — Provider LLM OpenAI-compatible, redaction e comando analyze base.
- [x] S1.3 — Hotfix redaction, blocco cloud senza redaction e caricamento prompt versionato. Review: `docs/reviews/S1.3-claude.md`.
- [x] S1.5 — Security hotfix: SecretStr, client locale senza proxy, policy ollama+loopback, loader prompt, gate canary self-tightening, report.sh senza modifiche all'indice (F4, F12-F17, F20). Review: `docs/reviews/S1.5-claude.md`.
- [x] S1.7 — Redaction hardening: bypass C32-C39, gate su byte grezzi, normalizzazione per riga senza falsificazione di righe (F18, F19, F21). Review: `docs/reviews/S1.7-claude.md` — APPROVED.

## Backlog Sprint 2 (dalle review S1)

- [ ] Switch a `prompts/analyze_v1.1.md` (F15) + validazione JSON dell'output con 1 retry.
- [ ] `report.py`: escape di evidence, link e immagini nel Markdown.
- [ ] `chunker.py` (usa `max_chunk_chars`).
- [ ] Canary SHOULD C40-C48 (`adv_05`), in ordine di priorita': valore di query string troncato da `%26`/`%3B`/`%20` (C41-C43), stringa di connessione con spazio (C48), escape JSON di lettere/quote (C40, C44, C46), CDATA (C47), Basic spezzato su due righe (C45).
- [ ] Falsi positivi su chiavi composte (`pass_count`, `ticket_count`) — F22.
- [ ] `report.sh`: filtrare la sezione git status con la stessa allowlist (F23).
- [ ] Decisione del planner: le rubriche MUST/SHOULD devono considerare i log DEBUG raccolti durante il troubleshooting?
