# Demo GIF for the README — render with: vhs docs/demo.tape  (from the repo root)
#
# Prerequisites (not recorded):
#   - otlog2fix installed and on PATH (pipx or .venv activated)
#   - Ollama running on localhost with `ollama pull qwen3:8b` done
# Input: tests/fixtures/01_cs_ora_tablespace.txt — 100% synthetic (synth.* users,
# RFC 5737 IPs, OTCS_SYNTH schema). No real data. The model's answer varies between
# runs: re-record until the output shows status, root cause and 3 fix steps, and
# check the GIF frame by frame before committing it.

Output docs/demo.gif

Require otlog2fix

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 720
Set Padding 20
Set TypingSpeed 40ms
Set Theme "Dracula"

Env OTLF_PROVIDER "ollama"
Env OTLF_BASE_URL "http://localhost:11434/v1"
Env OTLF_MODEL "qwen3:8b"
Env OTLF_REDACT "true"

# Neutral prompt and a scratch report path: no user name, host name or home path on screen.
Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type "head -n 7 tests/fixtures/01_cs_ora_tablespace.txt"
Sleep 300ms
Enter
Sleep 3s

Type "otlog2fix analyze tests/fixtures/01_cs_ora_tablespace.txt --md demo-report.md"
Sleep 300ms
Enter
# Local model latency: raise this if the answer is not complete in the recording.
Sleep 25s

Type "head -n 20 demo-report.md"
Sleep 300ms
Enter
Sleep 6s
