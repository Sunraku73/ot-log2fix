# OT-Log2Fix

CLI che analizza log OpenText (Content Server, AppWorks) con LLM locali (Ollama)
o cloud (OpenRouter) e produce un report Markdown: root cause + fix suggeriti.

> Stato: pre-alpha. Vedi [docs/PLAN.md](docs/PLAN.md) per la roadmap.

## Quickstart

    python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
    cp .env.example .env
    .venv/bin/otlog2fix version

## Modello di sicurezza

**In breve:** la redaction riduce il rischio, ma non lo azzera. Per log sensibili usa la modalita' locale.

### Cosa fa la redaction
- Prima di ogni chiamata al modello, `otlog2fix` rimuove password, token e ticket OpenText (`OTCSTicket`, `LLCookie`, `OTDSTicket`), header `Authorization`, API key, chiavi private PEM/PGP, credenziali in URL, JDBC e sqlplus, ed email. I valori vengono sostituiti da segnaposto `[REDACTED:<tipo>]`.
- Riconosce anche le forme codificate piu' comuni: percent-encoding, entita' HTML, escape JSON, valori spezzati su piu' righe, base64 sotto chiavi sensibili.
- Una riga con codifiche annidate oltre il limite di decodifica viene redatta per intero (`[REDACTED:opaque_line]`): nel dubbio si rimuove.
- La decodifica non crea mai righe nuove: un `%0A` dentro un campo non puo' falsificare un record di log.

### Cosa NON garantisce
- **La redaction e' best-effort, basata su pattern.** Non garantisce l'assenza di segreti nel testo inviato. Un segreto in un formato non previsto (chiave sconosciuta, codifica insolita, valore senza etichetta) puo' passare.
- La copertura minima e' fissata da un **canary gate** (`tests/fixtures/redaction_canaries.tsv`), che serve da soglia anti-regressione, non da prova di completezza:
  - `MUST`: segreti nelle forme tipiche dei log OpenText. Il build fallisce se uno solo trapela.
  - `SHOULD`: offuscamenti meno comuni, ancora scoperti e tracciati come `xfail` strict. Quando uno viene coperto, il test obbliga a promuoverlo a `MUST`.
- Nei log a livello DEBUG/trace (request body, header, dump di configurazione) compaiono piu' segreti e in piu' formati che a livello default: il rischio residuo e' piu' alto.

### Regole operative
| Scenario | Provider | Redaction |
|---|---|---|
| Log sensibili, di produzione o di clienti | `ollama` su `localhost`/`127.0.0.1`/`::1` | consigliata; disattivabile solo qui |
| Log sintetici o gia' anonimizzati | cloud (`openrouter`) | **obbligatoria**: con `OTLF_REDACT=false` e un provider non locale il comando termina con exit 1 prima di qualsiasi chiamata |

- Con provider locale il client HTTP ignora `HTTP(S)_PROXY`/`ALL_PROXY`, cosi' il log non esce dalla macchina passando per un proxy. "Locale" deve esserlo anche a valle: un gateway su localhost che inoltra al cloud (es. LiteLLM) annulla questa garanzia.
- Il contenuto del log e' trattato come **input non fidato**: viaggia JSON-encoded, tra delimitatori con nonce casuale, e il prompt di sistema vieta di eseguirne le istruzioni (difesa da prompt injection, non garanzia).
- Prima di usare un provider cloud, controlla a campione il testo redatto. Non committare mai log reali: vanno in `samples/private/` (gitignored).
- Per segnalare un bypass: aggiungi una fixture **sintetica** e una riga al manifest dei canary (vedi `tests/fixtures/README.md`).

## Licenza
MIT
