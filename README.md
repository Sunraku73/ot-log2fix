# OT-Log2Fix

Command-line triage for OpenText Content Server and AppWorks logs: an LLM reads the log and returns a probable root cause, the evidence lines and three fix steps.


> **Status: alpha (0.1).** CLI messages and reports are currently in **Italian**. English output is on the v0.2 roadmap.

## Example output

Real output of `otlog2fix analyze tests/fixtures/01_cs_ora_tablespace.txt --md report.md`, with local Ollama and `qwen3:8b`, on a synthetic Content Server log with Oracle `ORA-01653` errors. Below is the `report.md` file, unedited (Markdown source). Reports are currently in Italian.

````markdown
# Analisi del log

**File:** 01\_cs\_ora\_tablespace.txt
**Chunk:** 1 di 1
**Provider:** ollama · **Modello:** qwen3:8b
**Timestamp UTC:** 2026-11-15T11:45:34.673645+00:00

**Stato:** ok
**Confidenza:** medium

## Causa
Errore ORA-01653: il tablespace OTCS\_SYNTH\_DATA non ha spazio sufficiente per espandere le tabelle DVersData e DTreeCore. I tentativi di aggiungere versioni e creare documenti falliscono a causa della mancanza di spazio disco.

## Evidenze
```text
11/14/2026 09:12:31.912 [Thread 14] ERROR   ORA-01653: unable to extend table OTCS_SYNTH.DVERSDATA by 8192 in tablespace OTCS_SYNTH_DATA
11/14/2026 09:12:33.802 [Thread 9]  ERROR   ORA-01653: unable to extend table OTCS_SYNTH.DTREECORE by 1024 in tablespace OTCS_SYNTH_DATA
```

## Azioni
1. Verifica lo spazio disponibile nel tablespace OTCS\_SYNTH\_DATA e le dimensioni delle tabelle DVersData/DTreeCore
2. Espandi il tablespace incrementando la dimensione o aggiungendo nuovi file di dati
3. Monitora l'uso dello spazio e ottimizza la gestione dei dati \(es. purge vecchi versioni\)

## Contesto mancante
- Versione del Content Server
- Configurazione del tablespace OTCS\_SYNTH\_DATA
- Altri chunk del log per verificare pattern ricorrenti

**Injection rilevata:** no

## Note
Errori ORA-01653 ricorrenti su tablespace OTCS\_SYNTH\_DATA
````

The same content is printed to the terminal. Each evidence line is checked against the redacted log: it must match the start of a log line. The fix steps are suggestions: verify them before you act.

## Install

> **Windows: not yet verified on a real host.** The PowerShell commands in this README follow standard syntax and the test suite runs on `windows-latest` in CI, but nobody has yet walked through install and analysis on a Windows machine. Reports are welcome.

### Prerequisites

- **git**: `pipx` uses it to fetch the package from GitHub.
- **Python 3.10 or newer**.
- **pipx**: installs the CLI in its own isolated environment.

Ubuntu 22.04+ / Debian 12+:

    sudo apt update && sudo apt install -y git python3 pipx
    pipx ensurepath    # then open a new terminal

Other systems (Windows, macOS, other Linux distributions): see [pipx.pypa.io](https://pipx.pypa.io/stable/installation/) for pipx, [git-scm.com](https://git-scm.com/downloads) for git and [python.org](https://www.python.org/downloads/) for Python.

### Install the CLI

    pipx install git+https://github.com/Sunraku73/ot-log2fix.git
    otlog2fix version     # prints: OT-Log2Fix 0.1.0
    otlog2fix --help      # lists the commands: version, analyze

Configuration comes from environment variables (prefix `OTLF_`) or from a `.env` file **in the directory you run the command from**. See [`.env.example`](.env.example).

| Variable | Default | Meaning |
|---|---|---|
| `OTLF_PROVIDER` | `ollama` | `ollama` or any OpenAI-compatible provider name |
| `OTLF_BASE_URL` | `http://localhost:11434/v1` | provider endpoint |
| `OTLF_MODEL` | `qwen3:8b` | model name |
| `OTLF_API_KEY` | empty | required for cloud providers |
| `OTLF_TIMEOUT` | `300` | seconds to wait for the model, 10–3600 |
| `OTLF_ENCODING` | `utf-8` | encoding of the log file (see [Log encoding](#log-encoding)) |
| `OTLF_MAX_CHUNK_CHARS` | `12000` | chunk size, minimum 1000 |
| `OTLF_REDACT` | `true` | can be `false` only with local Ollama |

### Local model with Ollama

Local mode needs [Ollama](https://ollama.com/download), available for Linux, macOS and Windows.

    ollama pull qwen3:8b      # about 5 GB download
    ollama list               # qwen3:8b must be listed

To check that Ollama is running, query its API: it must answer with the list of models.

    curl http://localhost:11434/api/tags                  # bash
    Invoke-RestMethod http://localhost:11434/api/tags     # PowerShell

**Hardware.** Measured on the example log above (14 lines, about 2600 prompt tokens), Ollama 0.23.1, 3 runs or more per row:

| Model | NVIDIA GPU (24 GB VRAM) | CPU only (16 cores) |
|---|---|---|
| `qwen3:8b` (5.2 GB) | 6–13 s, valid answer in every run | 80–120 s, valid answer in every run |
| `qwen3:4b` (2.5 GB) | 20–37 s, valid answer in every run | 220–380 s, **no valid answer in 3 runs** |

The default timeout (`OTLF_TIMEOUT=300`) covers `qwen3:8b` on CPU. Longer logs take longer: raise it if you see a timeout.

Use `qwen3:8b`. `qwen3:4b` is smaller to download but **not** faster: it reasons for much longer than the 8b. On CPU it failed to produce a valid answer in our runs, so consider it only for a GPU with little memory.

## Quickstart

### Local with Ollama (logs never leave the machine)

The defaults already point to `http://localhost:11434/v1` and `qwen3:8b`, so no configuration is needed.

bash:

    otlog2fix analyze /path/to/thread.log --md report.md

Windows PowerShell (quote the path, especially if it contains spaces):

    otlog2fix analyze "C:\Logs\thread.log" --md report.md

### Cloud with OpenRouter (synthetic or anonymized logs only)

bash:

    export OTLF_PROVIDER=openrouter
    export OTLF_BASE_URL=https://openrouter.ai/api/v1
    export OTLF_API_KEY=<your-openrouter-key>
    export OTLF_MODEL=<model-id>
    otlog2fix analyze /path/to/thread.log --md report.md

Windows PowerShell (the variables last for the current window only):

    $env:OTLF_PROVIDER = "openrouter"
    $env:OTLF_BASE_URL = "https://openrouter.ai/api/v1"
    $env:OTLF_API_KEY  = "<your-openrouter-key>"
    $env:OTLF_MODEL    = "<model-id>"
    otlog2fix analyze "C:\Logs\thread.log" --md report.md

Pick any model listed on openrouter.ai/models. Redaction cannot be disabled with a cloud provider.

### Output

- **Terminal:** status, root cause, confidence, evidence lines, three fix steps and an injection flag.
- **`--md`:** the same content as Markdown, with file name, provider, model and a UTC timestamp.
- When the model lacks the information it needs, it must answer `NON HO ABBASTANZA CONTESTO` ("not enough context") and list what is missing, instead of inventing OScript functions or REST endpoints.
- **Invalid model output:** if the model returns invalid output twice, `otlog2fix` writes a **minimal report** instead of failing. The report says `NON HO ABBASTANZA CONTESTO`, gives three generic suggestions and quotes the first quotable line of the chunk as a reference, not as a diagnosis. Its exit code is `0`: check the report's status (`insufficient_context`) when scripting.
- **Exit codes:**
  - `0` success
  - `1` input or configuration error
  - `2` provider error, or the model returned invalid output twice and the analyzed chunk has no line that can be quoted (see [Troubleshooting](#troubleshooting))

## Log encoding

Logs are read as **UTF-8** by default. OpenText logs written on Windows servers are often in **CP1252** (Windows-1252). Such a file fails with `Errore decodifica con utf-8; imposta OTLF_ENCODING (es. cp1252 per log Windows).` (exit 1) and nothing is sent to the model. Set the encoding explicitly:

bash:

    OTLF_ENCODING=cp1252 otlog2fix analyze /path/to/thread.log

Windows PowerShell:

    $env:OTLF_ENCODING = "cp1252"
    otlog2fix analyze "C:\Logs\thread.log"

There is no automatic guessing on purpose. CP1252 decodes almost any byte sequence without error, so a wrong guess would not fail: it would silently turn characters into different ones, in what the model reads and in the evidence quoted in the report. An explicit setting fails loudly instead.

## Which logs to point at

The prompt is written for **OpenText** products: Content Server, AppWorks and OTDS. The test fixtures currently cover these cases:

- **Content Server:** database errors (e.g. Oracle `ORA-` codes), node permission errors, license errors, OScript stack traces.
- **AppWorks:** REST API authentication errors (HTTP 401).

There are no OTDS fixtures yet.

`otlog2fix` accepts any plain-text log up to 10 MiB. On logs from other products the answer is more often `NON HO ABBASTANZA CONTESTO` ("not enough context"). This is the intended behavior: the prompt tells the model to say so instead of inventing a diagnosis.

> **TODO (maintainer):** the names and default locations of the log files to analyze for each product are not documented yet. Until then, use the log that contains the error you are investigating, cut down to the relevant time window.

## Providers

| Provider | `OTLF_PROVIDER` | `OTLF_BASE_URL` | API key | Redaction |
|---|---|---|---|---|
| Ollama (local) | `ollama` | `http://localhost:11434/v1` | none | on by default; may be disabled only here |
| OpenRouter (cloud) | `openrouter` | `https://openrouter.ai/api/v1` | required | mandatory |
| Other OpenAI-compatible endpoint | any | its `/v1` URL | as required | mandatory unless `ollama` on loopback |

"Local" means provider `ollama` with host `localhost`, `127.0.0.1` or `::1`. Every other combination is treated as remote.

## Security model

**In short:** redaction reduces the risk, it does not remove it. For sensitive logs, use local mode.

### What redaction does

- **Before every model call,** `otlog2fix` removes:
  - passwords, tokens and OpenText tickets (`OTCSTicket`, `LLCookie`, `OTDSTicket`)
  - `Authorization` headers and API keys
  - PEM/PGP private keys
  - credentials in URLs, JDBC strings and sqlplus commands
  - email addresses

  Values are replaced by `[REDACTED:<type>]` placeholders.
- **Common encodings** are recognized too: percent-encoding, HTML entities, JSON escapes, values split across lines, and base64 under sensitive keys.
- **Nested encodings:** a line encoded more deeply than the decoding limit is redacted entirely (`[REDACTED:opaque_line]`). When in doubt, it is removed.
- **No forged lines:** decoding never creates new lines, so a `%0A` inside a field cannot forge a log record.

### What it does NOT guarantee

- **Redaction is best-effort and pattern-based.** It does not guarantee that the text sent is free of secrets. A secret in an unexpected shape can get through: an unknown key, an unusual encoding, or a value with no label.
- Minimum coverage is pinned by a **canary gate** (`tests/fixtures/redaction_canaries.tsv`). The gate is a regression threshold, not a proof of completeness:
  - `MUST`: secrets in the shapes typical of OpenText logs. The build fails if a single one leaks.
  - `SHOULD`: rarer obfuscations that are not covered yet, tracked as strict `xfail`. When one becomes covered, the test forces its promotion to `MUST`.
- **DEBUG/trace logs carry more risk.** At those levels (request bodies, headers, configuration dumps) secrets appear more often and in more shapes than at default levels.

### Operating rules

| Scenario | Provider | Redaction |
|---|---|---|
| Sensitive, production or customer logs | `ollama` on `localhost`/`127.0.0.1`/`::1` | recommended; can be disabled only here |
| Synthetic or already anonymized logs | cloud (e.g. `openrouter`) | **mandatory**: with `OTLF_REDACT=false` and a non-local provider the command exits with code 1 before any call |

- **Proxies are ignored locally.** With a local provider the HTTP client ignores `HTTP(S)_PROXY`/`ALL_PROXY`, so the log cannot leave the machine through a proxy.
- **"Local" must be local all the way down.** A localhost gateway that forwards to the cloud (e.g. LiteLLM) voids this guarantee.
- **The log is untrusted input.** It travels JSON-encoded between delimiters with a random nonce, and the system prompt forbids following instructions found in it. This mitigates prompt injection; it does not prevent it.
- **Spot-check before going to the cloud.** Review the redacted text before using a cloud provider. Never commit real logs: keep them in `samples/private/` (gitignored).
- **Reporting a bypass:** see [SECURITY.md](SECURITY.md).

## Troubleshooting

The messages are in Italian; the table quotes them as printed.

| Symptom (exit code, message) | Cause | Action |
|---|---|---|
| `2` `Provider non raggiungibile su http://localhost:11434. Verifica che Ollama sia attivo.` | Ollama is not running, or `OTLF_BASE_URL` is wrong | Start Ollama and check it with `curl http://localhost:11434/api/tags`. Check `OTLF_BASE_URL` in the environment and in `.env` |
| `2` `Timeout del provider dopo 300s. Su CPU aumenta OTLF_TIMEOUT (es. 600).` | The model did not answer within `OTLF_TIMEOUT` seconds: likely on CPU-only machines or with long logs | Raise `OTLF_TIMEOUT` (up to 3600), e.g. `OTLF_TIMEOUT=600` |
| `2` `Errore provider HTTP 404. Modello non trovato. Esegui: ollama pull qwen3:8b` | The model is not downloaded, or `OTLF_MODEL` is misspelled | Run the suggested `ollama pull`, then `ollama list` to check the exact name |
| `2` `Errore provider HTTP <code>` (other codes) | The provider rejected the request, e.g. `401` for a wrong API key | Check `OTLF_API_KEY`, `OTLF_MODEL` and `OTLF_BASE_URL` |
| `0` with a minimal report: cause `NON HO ABBASTANZA CONTESTO`, notes `Il provider non ha restituito una risposta JSON valida dopo due tentativi…` | The model returned invalid JSON twice: more likely with small models or logs outside OpenText. The three suggestions are generic, not a diagnosis | If it happens often, try a larger model (e.g. `qwen3:8b` instead of `qwen3:4b`) or extract the relevant portion of the log |
| `2` `Risposta del provider non valida e nessuna riga citabile nel chunk: impossibile produrre un report.` | Invalid JSON twice, and the analyzed chunk has no line that can be quoted as evidence (e.g. only whitespace, or lines made of a short prefix followed by long padding) | Extract the relevant portion of the log, or remove the padding, and retry |
| `1` `Errore decodifica con utf-8; imposta OTLF_ENCODING (es. cp1252 per log Windows).` | The log is not UTF-8 | Set `OTLF_ENCODING`, see [Log encoding](#log-encoding) |
| `1` `Il file supera il limite di 10 MiB.` | The log is larger than 10 MiB | Extract the relevant portion, e.g. the time window around the error |
| `1` `La redaction può essere disabilitata solo con provider locale ollama.` | `OTLF_REDACT=false` with a cloud or non-loopback provider | This is the security policy, not a bug. Keep redaction on, or use local Ollama |
| `1` `OTLF_MAX_CHUNK_CHARS: deve essere un intero con valore minimo 1000.` | `OTLF_MAX_CHUNK_CHARS` is below 1000 or not a number | Use a value of at least 1000 (default 12000) |
| `1` `OTLF_<NAME>: valore non valido.` | A setting has an invalid value (e.g. `OTLF_TIMEOUT` outside 10–3600, an unknown `OTLF_ENCODING`) | Fix the named variable; the value itself is never printed |
| `1` `Errore lettura file: …` | Wrong path or missing file | Check the path (quote it in PowerShell) |

## Known limits

- **Partial analysis.** A log is split into chunks of `OTLF_MAX_CHUNK_CHARS` (default 12000, minimum 1000), and **only one chunk is analyzed**: the one with the most `ERROR`/`FATAL` levels, the most recent on ties. The report says so ("chunk X of Y"). The selection heuristic can be steered by crafted log content.
- **Best-effort redaction** (see above).
- **Suggestions, not answers.** Fix steps are suggestions to verify. The model can be wrong even with `high` confidence, and evidence lines are checked to exist in the log, not to be the right ones.
- **Italian-only output** for now.

## Roadmap (v0.2)

These are plans, not commitments:

- Analyze all chunks and merge the results, instead of picking one (removes the selection heuristic).
- English CLI and report output.
- Package on PyPI.
- Promote `SHOULD` canaries to `MUST` when backed by real anonymized captures.

## Development

Linux / macOS:

    python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
    make check   # ruff + pytest, including the canary gate

Windows PowerShell (no `make`; not yet verified on a real host):

    py -m venv .venv
    .venv\Scripts\activate
    pip install -e ".[dev]"
    ruff check src tests
    pytest -q

`scripts/report.sh` and `docs/demo.tape` (VHS) are Unix-only tools for maintainers; they are not needed to use or test the CLI.

Review history and decisions are in [`docs/reviews/`](docs/reviews/) and [`docs/PLAN.md`](docs/PLAN.md) (in Italian).

## License

MIT, see [LICENSE](LICENSE).

## Support

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/G1J72ANIUV)

---

Not affiliated with or endorsed by OpenText. OpenText, Content Server and AppWorks are trademarks of OpenText Corporation.
