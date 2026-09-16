#!/usr/bin/env bash
# Put five known bugs into each clean program.
#
# A different harness and a different model from the one that wrote the
# programs, and neither has been told anything about assay: the point of the
# set is that the defects were not chosen by the thing being measured.
#
# Usage: inject.sh <clean-dir> <output-dir>   (CEREBRAS_API_KEY must be set)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLEAN="${1:?usage: inject.sh <clean-dir> <output-dir>}"
OUT="${2:?usage: inject.sh <clean-dir> <output-dir>}"
OPENCODE="${OPENCODE:-opencode}"
MODEL="${MODEL:-cerebras/qwen-3.8-27b}"
PROMPT="$(cat "$HERE/inject-prompt.txt")"

for src in "$CLEAN"/*/; do
  name="$(basename "$src")"
  dir="$OUT/$name"
  [ -f "$dir/bugs.md" ] && { echo "  $name already done"; continue; }
  rm -rf "$dir"; mkdir -p "$dir"
  cp "$src/index.html" "$dir/index.html"
  t0=$SECONDS
  ( cd "$dir" && timeout 600 "$OPENCODE" run --model "$MODEL" "$PROMPT" \
      >/dev/null 2>&1 </dev/null )
  rm -rf "$dir/.opencode" "$dir/AGENTS.md" 2>/dev/null
  if [ -f "$dir/bugs.md" ]; then
    planted=$(grep -c '^\s*[0-9]\.' "$dir/bugs.md" || true)
    echo "  $name  $planted entries  $((SECONDS-t0))s"
  else
    echo "  !! $name no bugs.md"
  fi
done
