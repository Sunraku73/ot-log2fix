# Piano

Owner del file: Claude (da S1.6). Un task si spunta solo dopo il verdetto APPROVED della review.

## Sprint 1 — chiuso (2026-11-14)

- [x] S1.1 — Provider LLM OpenAI-compatible, redaction e comando analyze base.
- [x] S1.3 — Hotfix redaction, blocco cloud senza redaction e caricamento prompt versionato. Review: `docs/reviews/S1.3-claude.md`.
- [x] S1.5 — Security hotfix: SecretStr, client locale senza proxy, policy ollama+loopback, loader prompt, gate canary self-tightening, report.sh senza modifiche all'indice (F4, F12-F17, F20). Review: `docs/reviews/S1.5-claude.md`.
- [x] S1.7 — Redaction hardening: bypass C32-C39, gate su byte grezzi, normalizzazione per riga senza falsificazione di righe (F18, F19, F21). Review: `docs/reviews/S1.7-claude.md` — APPROVED.

## Sprint 2 — chiuso (2026-11-14)

- [x] S2.0 — Redaction batch: canary C41-C48 promossi a MUST, falsi positivi su chiavi di conteggio (F22), fixture senza pattern di push protection (F11). Review: `docs/reviews/S2-claude.md`.
- [x] S2.1 — Validazione schema dell'output con 1 retry, report rich/Markdown, chunker su `max_chunk_chars`, switch a prompt v1.1 (F15). Review: `docs/reviews/S2-claude.md`. Hardening completato in S2.3/S2.4/S2.6.
- [x] `report.sh` v3: allowlist anche sullo status e baseline `last-reviewed` (F23, F24, commit `ae66d7e`).
- [x] S2.3 — Integrità del report: evidence intera o prefisso ≥ 40, metadati e banner di analisi parziale, fence dinamico, cap dei campi (F25-F33; F33 confutato). Review: `docs/reviews/S2.4-claude.md` — APPROVED.
- [x] S2.4 — Sicurezza del report: caratteri di controllo neutralizzati, schemi URL inerti, close del client, budget encoded (F25, F26, F29-F32, F34-F36). Review: `docs/reviews/S2.4-claude.md` — CHANGES_REQUESTED per F37, chiuso da S2.6.
- [x] S2.6 — Chunker lineare (F37) e guard `OTLF_MAX_CHUNK_CHARS >= 1000` (F38). Review: `docs/reviews/S2.6-claude.md` — APPROVED.

Finding chiusi in S2: F11, F22, F23, F24, F25, F26, F27, F28, F29, F30, F31, F32, F33 (confutato), F34, F35, F36, F37, F38.

### Rubrica MUST/SHOULD (decisione del planner, S2)

Un nuovo canary MUST si aggiunge solo con evidenza da capture reali anonimizzate, inclusi log DEBUG raccolti durante il troubleshooting se arrivano da capture reali. Offuscamenti ipotetici o esotici restano SHOULD in backlog (xfail strict).

## Sprint 3 — rilascio 0.1

- [x] Repo remoto pubblico `github.com/Sunraku73/ot-log2fix`; storia riscritta con `git filter-repo` prima del primo push (F11; nota sugli SHA in `docs/reviews/README.md`, F43).
- [x] S3.1 — Messaggi di configurazione per variabile senza valori (F41), `encoded_length` unica (F42), CI con matrice 3.10-3.13, metadati di packaging. Review: `docs/reviews/S3-claude.md` — CHANGES_REQUESTED (F39 email), chiuso da S3.3.
- [x] S3.2 — Docs di lancio: README EN, `SECURITY.md`, `docs/demo.tape`, `docs/launch-copy.md`, indice review (F43).
- [x] S3.3 — Autolink email neutralizzati (F39, verificato su GitHub e cmark-gfm), margine virgolette testato (F44), job perf solo manuale con redaction (F45), URL canonici (F46). Review: `docs/reviews/S3.4-claude.md` — APPROVED.

- [x] S3.5 — Hygiene CI (`ruff` bloccato, `permissions: contents: read`, timeout job) e rimozione duplicato perf (F48, F50). Review: `docs/reviews/S3.8-claude.md` — APPROVED.
- [x] S3.6 — README per nuovi utenti, verificato sul percorso pipx reale. Review: `docs/reviews/S3.6-claude.md`.
- [x] S3.7 — Timeout configurabile `OTLF_TIMEOUT` (F51), help `--md` (F53), suggerimento 404 (F54), errori provider distinti (F55), `OTLF_ENCODING` (F56), CI Windows (F57). Review: `docs/reviews/S3.8-claude.md` — APPROVED.
- [x] S3.8 — Esperimento F52 (thinking qwen3): **non adottato** (CPU sempre ≥ 54 s, diagnosi meno precisa); docs cross-platform ed encoding (F58).

Finding chiusi in S3: F11 (push), F39, F41, F42, F43, F44, F45, F46, F47 (tag riportato su `da681fa`), F48, F50, F51, F52 (non adottato), F53, F54, F55, F56, F57, F58.

### Prima del lancio

- [ ] **Gate di lancio:** nomi e posizioni reali dei log OpenText nella sezione "Which logs to point at" del README (segnaposto `TODO (maintainer)`, da fornire Emilio).
- [ ] Al primo push: verificare l'esito del job `windows-latest` in CI (F57 chiuso solo per lettura).
- [ ] Verificare installazione e analisi su un host Windows reale; poi rimuovere l'avviso "not yet verified" dal README.
- [ ] Registrare `docs/demo.gif` con `docs/demo.tape` (Ollama locale, fixture sintetica) e verificarla frame per frame.
- [ ] Abilitare il private vulnerability reporting su GitHub (citato in `SECURITY.md`).

## Backlog v0.2

- [ ] **F40 — by-design:** la selezione del chunk è orientabile con apici singoli o senza quote. Soluzione prevista: analisi di tutti i chunk con merge dei risultati.
- [ ] Output del CLI e del report in inglese.
- [ ] Pacchetto su PyPI.
- [ ] Action pinnate per SHA (residuo facoltativo di F48).
- [ ] F49 — Metadato licenza: `license = "MIT"` + `license-files`, `setuptools>=77`.
- [ ] F59 — `OTLF_ENCODING` con codec non testuali (`rot13`, `base64`, `hex`) → traceback (`config.py`).
- [ ] F60 — Suggerimento `ollama pull` su 404 anche con provider non Ollama (`providers.py`).
- [ ] F61 — Risposta 200 non JSON → traceback ed exit 1 invece di 2 (`providers.py`, preesistente).
- [ ] F62 — Latenza CPU dominata dal prefill (~2600 token): prompt più corto `analyze_v1.2` da misurare; `reasoning_effort=none` eventualmente opt-in solo per `ollama`.
- [ ] Canary SHOULD C50, C51, C53, C54: promuoverli solo con evidenza da capture reali (rubrica sopra).
