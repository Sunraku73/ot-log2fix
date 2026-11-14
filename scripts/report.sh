#!/usr/bin/env bash
# Bundle di review per il planner (Qwen). NON tocca l'indice git.
# Baseline: tag 'last-reviewed'; fallback HEAD~3, poi root. Override: REVIEW_BASE=<ref>
set -euo pipefail
cd "$(dirname "$0")/.."
OUT_DIR="${WORK_DIR:-$HOME/Downloads}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/otlf-review-$(date +%Y%m%d-%H%M%S).md"
PATHS=(src tests docs scripts pyproject.toml Makefile README.md LICENSE .env.example .gitignore)

BASE="${REVIEW_BASE:-}"
if [ -z "$BASE" ]; then
  BASE=$(git rev-parse --verify -q last-reviewed || git rev-parse --verify -q HEAD~3 || git rev-list --max-parents=0 HEAD | tail -1)
fi
if [ -z "$BASE" ]; then echo "Baseline non trovato" >&2; exit 1; fi

allowlisted() {
  case "$1" in
    src/*|tests/*|docs/*|scripts/*) return 0 ;;
    pyproject.toml|Makefile|README.md|LICENSE|.env.example|.gitignore) return 0 ;;
    *) return 1 ;;
  esac
}

{
  echo "# OT-Log2Fix — review bundle $(date -Iseconds)"
  echo "Baseline: $(git log --oneline -1 "$BASE")"

  echo; echo "## Commit da revieware"; echo '```'
  git log --oneline --decorate "$BASE"..HEAD; echo '```'

  echo; echo "## Diffstat commit"; echo '```'
  git diff --stat "$BASE" HEAD -- "${PATHS[@]}"; echo '```'

  echo; echo "## Diff commit (baseline..HEAD)"; echo '```diff'
  git diff "$BASE" HEAD -- "${PATHS[@]}"; echo '```'

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

  echo; echo "## Working tree vs HEAD"; echo '```diff'
  git diff HEAD -- "${PATHS[@]}"; echo '```'

  echo; echo "## File nuovi (allowlist, <1 MiB)"
  while IFS= read -r f; do
    allowlisted "$f" || continue
    if [ "$(stat -c%s "$f")" -ge 1048576 ]; then echo "SALTATO (>1MiB): $f"; continue; fi
    echo '```diff'; git diff --no-index -- /dev/null "$f" || true; echo '```'
  done < <(git ls-files --others --exclude-standard)

  echo; echo "## make check"; echo '```'; make check 2>&1 || true; echo '```'

  echo; echo "## Review nuove o modificate dal baseline"
  REVIEWS=$({ git diff --name-only "$BASE" HEAD -- docs/reviews; git ls-files --others --exclude-standard -- docs/reviews; } | sort -u)
  if [ -n "$REVIEWS" ]; then
    while IFS= read -r f; do
      if [ -f "$f" ]; then echo; cat "$f"; fi
    done <<< "$REVIEWS"
  else
    echo "(nessuna review nuova rispetto al baseline)"
  fi
} > "$OUT"
echo "Bundle creato: $OUT"
