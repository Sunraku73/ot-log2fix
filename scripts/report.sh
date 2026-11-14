#!/usr/bin/env bash
# Bundle di review per il planner (Qwen). NON tocca l'indice git.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT_DIR="${WORK_DIR:-$HOME/Downloads}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/otlf-review-$(date +%Y%m%d-%H%M%S).md"
BASE=$(git rev-parse --verify -q HEAD || git hash-object -t tree /dev/null)
PATHS=(src tests docs scripts pyproject.toml Makefile README.md LICENSE .env.example .gitignore)

allowlisted() {
  case "$1" in
    src/*|tests/*|docs/*|scripts/*) return 0 ;;
    pyproject.toml|Makefile|README.md|LICENSE|.env.example|.gitignore) return 0 ;;
    *) return 1 ;;
  esac
}

{
  echo "# OT-Log2Fix — review bundle $(date -Iseconds)"
  echo; echo "## Git status (allowlist)"; echo '```'
  excluded=0
  while IFS= read -r line; do
    if [ -z "$line" ]; then continue; fi
    p="${line:3}"
    case "$p" in *" -> "*) p="${p##* -> }";; esac
    if allowlisted "$p"; then printf '%s\n' "$line"; else excluded=$((excluded+1)); fi
  done < <(git -c core.quotepath=false status --short)
  echo "($excluded file non in allowlist esclusi)"
  echo '```'
  echo; echo "## Diff tracked vs HEAD"; echo '```diff'
  git diff "$BASE" -- "${PATHS[@]}"; echo '```'
  echo; echo "## File nuovi (allowlist, <1 MiB)"
  while IFS= read -r f; do
    allowlisted "$f" || continue
    if [ "$(stat -c%s "$f")" -ge 1048576 ]; then echo "SALTATO (>1MiB): $f"; continue; fi
    echo '```diff'; git diff --no-index -- /dev/null "$f" || true; echo '```'
  done < <(git ls-files --others --exclude-standard)
  echo; echo "## make check"; echo '```'; make check 2>&1 || true; echo '```'
  if compgen -G "docs/reviews/*.md" > /dev/null; then
    echo; echo "## Risposte agenti"; cat docs/reviews/*.md
  fi
} > "$OUT"
echo "Bundle creato: $OUT"
