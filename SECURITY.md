# Security policy

## Supported versions

Only the latest `0.1.x` release on `main` receives fixes.

## Reporting a redaction bypass

A bypass is a secret that survives `redact()` and would be sent to the model. Report it as a test case, never as a real secret:

1. **Build a 100% synthetic sample.** Write the shortest log line that shows the bypass. Use fake values containing a marker such as `CANARY<nn>`, hosts under `example.invalid`, and IPs from `192.0.2.0/24`. Never paste a real password, ticket, key, host name or customer log, not even partially masked.
2. **Add it as a fixture** in `tests/fixtures/` (`.txt` extension) and add a row to `tests/fixtures/redaction_canaries.tsv`:

       <id>	<MUST|SHOULD>	<fixture file>	<short vector description>	<string that must not survive>

   See `tests/fixtures/README.md` for the conventions.
3. **Open a pull request or an issue** with the fixture. Because the sample is synthetic, a public report is fine: it shows a pattern, not a secret.

`MUST` or `SHOULD` is decided in review. A new `MUST` needs evidence that the shape appears in real (anonymized) OpenText logs. Exotic or hypothetical obfuscations are tracked as `SHOULD`.

## Reporting anything else

For issues that are not a redaction pattern, use GitHub's private vulnerability reporting (**Security → Report a vulnerability**). Examples: a path that sends data to a remote provider while redaction is off, a way around the local-only policy, or code execution through a crafted log. Do not open a public issue for these.

## What is guaranteed

- **No unredacted cloud calls.** With redaction disabled, the tool refuses to call any provider other than `ollama` on `localhost`/`127.0.0.1`/`::1`, and exits with code 1 before any network call.
- **No proxies locally.** With a local provider, `HTTP(S)_PROXY` and `ALL_PROXY` are ignored.
- **The canary gate is a regression threshold.** Every `MUST` row in `tests/fixtures/redaction_canaries.tsv` is checked on every test run, and the build fails if one leaks. A known bypass, once fixed, stays fixed.
- **Untrusted log content.** The log goes to the model JSON-encoded, between delimiters with a per-request random nonce.
- **Inert model output.** In the Markdown report, links, images, HTML and URL schemes are neutralized outside the evidence block. The evidence block reproduces log lines verbatim inside a code fence.

## What is NOT guaranteed

- **Complete redaction.** It is pattern-based and best-effort. A secret in a shape the patterns do not know (unlabelled value, unknown key, unusual encoding) can pass. Passing the canary gate means "no known regression", not "no secrets".
- **Immunity to prompt injection.** The prompt tells the model to treat the log as data. A model can still be steered by crafted log content; the report flags suspected injection but may miss it.
- **Correct diagnoses.** Root causes and fix steps are suggestions and must be verified before acting on them.
- **Downstream locality.** A "local" endpoint that forwards to a cloud service (e.g. a localhost gateway) breaks the local-only assumption. The tool cannot detect this.

If logs must not leave the machine, use local Ollama, and spot-check the redacted text before using any cloud provider.
