# OT-Log2Fix

Command-line triage for OpenText Content Server and AppWorks logs: an LLM reads the log and returns a probable root cause, the evidence lines and three fix steps.

![demo](docs/demo.gif)

> **Status: alpha (0.1).** CLI messages and reports are currently in **Italian**. English output is on the v0.2 roadmap.

## Install

Requires Python 3.10+.

    pipx install git+https://github.com/Sunraku73/ot-log2fix.git
    otlog2fix version

Configuration comes from environment variables (prefix `OTLF_`) or from a `.env` file in the current directory. See [`.env.example`](.env.example).

## Quickstart

### Local with Ollama (logs never leave the machine)

    ollama pull qwen3:8b
    otlog2fix analyze /path/to/thread.log --md report.md

The defaults already point to `http://localhost:11434/v1` and `qwen3:8b`.

### Cloud with OpenRouter (synthetic or anonymized logs only)

    export OTLF_PROVIDER=openrouter
    export OTLF_BASE_URL=https://openrouter.ai/api/v1
    export OTLF_API_KEY=<your-openrouter-key>
    export OTLF_MODEL=<model-id>
    otlog2fix analyze /path/to/thread.log --md report.md

Pick any model listed on openrouter.ai/models. Redaction cannot be disabled with a cloud provider.

### Output

- **Terminal:** status, root cause, confidence, evidence lines, three fix steps and an injection flag.
- **`--md`:** the same content as Markdown, with file name, provider, model and a UTC timestamp.
- When the model lacks the information it needs, it must answer `NON HO ABBASTANZA CONTESTO` ("not enough context") and list what is missing, instead of inventing OScript functions or REST endpoints.
- **Exit codes:**
  - `0` success
  - `1` input or configuration error
  - `2` provider error, or the model returned invalid output twice

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

    python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
    make check   # ruff + pytest, including the canary gate

Review history and decisions are in [`docs/reviews/`](docs/reviews/) and [`docs/PLAN.md`](docs/PLAN.md) (in Italian).

## License

MIT, see [LICENSE](LICENSE).

## Support

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/G1J72ANIUV)

---

Not affiliated with or endorsed by OpenText. OpenText, Content Server and AppWorks are trademarks of OpenText Corporation.
