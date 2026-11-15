# Launch copy — drafts (S3.2)

Bozze da rivedere prima di pubblicare. Da fare prima del lancio:
- registrare `docs/demo.gif`
- chiudere F39 (S3.3)

Regola comune ai tre testi: nessuna promessa di completezza; output in italiano dichiarato.

---

## 1. LinkedIn (OpenText consultants)

I've released OT-Log2Fix, a small open-source CLI for first-pass triage of OpenText Content Server and AppWorks logs.

You point it at a thread log. A local LLM (via Ollama) returns:
- a probable root cause
- the log lines it relies on
- three fix steps to verify

When the log doesn't contain enough to answer, it is instructed to say so instead of inventing OScript calls or REST endpoints.

The part I cared most about: **logs don't leave your machine** in local mode. Before anything reaches a model, credentials are redacted: passwords, OTCSTicket/LLCookie/OTDSTicket, Authorization headers, JDBC and URL credentials. Cloud providers are allowed only with redaction on.

What it is not:
- **Not a replacement for reading the log.** It analyzes one chunk of large logs, not the whole file.
- **Not airtight redaction.** It is pattern-based and best-effort.
- **Not localized yet.** Output is currently in Italian; English is next.

It's free (MIT). If you work with OTCS logs, I'd value feedback on real failure patterns it misses. Please don't send me actual logs: describe the pattern or share a synthetic line.

github.com/Sunraku73/ot-log2fix

Not affiliated with or endorsed by OpenText.

---

## 2. Show HN

**Title:** Show HN: OT-Log2Fix – triage OpenText Content Server logs with a local LLM

**Text:**

OT-Log2Fix is a Python CLI that reads an OpenText Content Server or AppWorks log and asks an LLM for a root cause, evidence lines and three fix steps. It defaults to Ollama on localhost, so the log stays on the machine.

These logs routinely contain tickets, passwords and connection strings, so most of the work went into the boring parts.

**Redaction:**
- Runs before every call.
- Decodes percent, HTML and JSON escapes per line, without letting a decoded `%0A` forge a new log line.
- Backed by a canary test set. Any regression on a "MUST" case fails the build.
- It is still pattern-based, and the README says so plainly.

**Local-only policy:**
- Turning redaction off is only allowed with `ollama` on a loopback host.
- In that mode the HTTP client ignores proxy env vars.

**Untrusted log:**
- The log is passed JSON-encoded inside delimiters with a per-request nonce.
- The model's JSON is schema-validated: every evidence line must exist in the log.
- The Markdown report neutralizes links, images and HTML from model output.

**Known limits:**
- Large logs are chunked and only one chunk (the most ERROR-heavy) is analyzed.
- The selection heuristic can be gamed.
- Output is Italian for now.
- Diagnoses are suggestions, not answers.

Built mostly as an exercise in making an LLM tool safe to point at sensitive logs. I'd appreciate critique of the threat model.

https://github.com/Sunraku73/ot-log2fix

---

## 3. r/devops

**Title:** Open-source CLI for LLM triage of OpenText logs, local-first with redaction (feedback welcome)

**Body:**

If you support OpenText Content Server or AppWorks, you know the routine: a large thread log, an ORA- error somewhere, and a ticket waiting.

I wrote **OT-Log2Fix** to do the first pass. It sends the log to an LLM and gets back a probable root cause, the supporting lines and three fix steps.

- **Local by default:** Ollama on localhost; the log doesn't leave the box.
- **Redaction before any call:** passwords, OT tickets, auth headers, JDBC and URL credentials, PEM keys, emails. There's a canary test suite so known bypasses can't come back.
- **Cloud is opt-in** (OpenRouter or any OpenAI-compatible endpoint), and only with redaction on. The tool refuses otherwise.
- **Exit codes** are 0/1/2/3 (3 = fallback report, no analysis), so it can sit in a script.

Limits, up front:
- **Partial analysis:** only one chunk of a large log is analyzed.
- **Redaction is best-effort:** check the redacted text before using a cloud model.
- **Italian output** (English is on the roadmap).
- It suggests; you verify.

MIT, Python 3.10+: `pipx install git+https://github.com/Sunraku73/ot-log2fix.git`

Interested in failure patterns it gets wrong. Please share them as synthetic lines, never real logs.

Not affiliated with OpenText.
