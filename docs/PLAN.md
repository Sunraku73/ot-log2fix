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

## Backlog Sprint 3

- [ ] **F39 — launch blocker:** `www.` ed email restano autolink GFM cliccabili nel report Markdown (`report.py`).
- [ ] **F40 — by-design:** la selezione del chunk è orientabile con apici singoli o senza quote. Da decidere: colonna del livello di log oppure analisi di tutti i chunk.
- [ ] F41 — Messaggio di configurazione non valida senza nome della variabile, eccetto `OTLF_MAX_CHUNK_CHARS` (`cli.py`).
- [ ] F42 — Test: asserzione di budget non discriminante nel test CLI; `measure` duplicata nei test invece di essere importata.
- [ ] Canary SHOULD C50, C51, C53, C54: promuoverli solo con evidenza da capture reali (rubrica sopra).
- [ ] Repo remoto e push (da autorizzare in S3).
