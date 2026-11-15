# Review

> **Nota sugli SHA (F43).** Prima del primo push la storia del repository è stata riscritta con `git filter-repo`, per rimuovere una chiave **sintetica** che attivava la push protection di GitHub. Gli SHA citati nelle review fino a S2.7 incluso si riferiscono alla storia locale pre-riscrittura e **non sono risolvibili nel repo pubblico**. Per ritrovare un commit cercate il messaggio (es. `git log --grep "S2.6"`), non lo SHA. Le review da S3 in poi citano gli SHA pubblici.

| File | Task | Commit revisionati (messaggio) | Verdetto |
|---|---|---|---|
| `S1.1-checklist.md` | S1.2 | checklist per S1.1 | — |
| `S1.3-claude.md` | S1.4 | S1.3 hotfix redaction | CHANGES_REQUESTED |
| `S1.5-claude.md` | S1.6 | S1.5 security hotfix | CHANGES_REQUESTED (poi chiuso in S1.7) |
| `S1.7-claude.md` | S1.8 | `fix: S1.7 redaction hardening (F18,F19,F21)` | APPROVED |
| `S2-claude.md` | S2.2 | `fix: S2.0 redaction batch …` (APPROVED), `feat: S2.1 schema validation …` (CHANGES_REQUESTED) | — |
| `S2.4-claude.md` | S2.5 | `fix: S2.3 report integrity …` (APPROVED), `fix: S2.4 report safety …` (CHANGES_REQUESTED) | — |
| `S2.6-claude.md` | S2.7 | `fix: S2.6 chunker lineare e guard config (F37,F38)` | APPROVED |
| `S3-claude.md` | S3.2 | `fix: S3.1 autolink residui, messaggi config, test (F39,F41,F42) + CI/packaging` | CHANGES_REQUESTED (F39 email) |
| `S3.4-claude.md` | S3.4 | `fix: S3.3 autolink email, budget margin, CI perf manuale, URL canonici (F39,F44,F45,F46)` | APPROVED |
| `S3.6-claude.md` | S3.6 | README per nuovi utenti (solo docs) + prova percorso utente | APPROVED (F51 MAJOR a Codex) |
| `S3.8-claude.md` | S3.8 | `chore: CI hardening …(F48,F50)`, `fix: S3.7 timeout configurabile …(F51,F53-F57)` + esperimento F52 | APPROVED |
| `S3.5-claude.md` | S3.5 (task) | round 1: fallback assente; round 2: `feat: S3.4 fallback graceful …`, `fix: S3.4b fallback senza eccezioni …` | round 1–2 CHANGES_REQUESTED; round 3 (`fix: S3.5r3 provenienza del fallback e exit 3 …`) APPROVED |
