#!/usr/bin/env bash
# Write the ten clean programs of the planted-bug set.
#
# The generator is the same harness and model the 225-program benchmark used,
# so a program here is the same kind of artefact as a program there. What is
# different is what happens next: `inject.sh` puts known bugs into a copy.
#
# Usage: generate.sh <output-dir>       (CEREBRAS_API_KEY must be set)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?usage: generate.sh <output-dir>}"
DSH="${DSH:-dsh}"
PATCH="${PATCH:-$HERE/cerebras.patch.yml}"

n=0
while IFS='|' read -r slug objective; do
  [ -z "$slug" ] && continue
  n=$((n + 1))
  dir="$OUT/$(printf '%02d' "$n")_${slug}"
  [ -f "$dir/index.html" ] && { echo "  $(basename "$dir") already there"; continue; }
  mkdir -p "$dir"
  t0=$SECONDS
  ( cd "$dir" && timeout 600 "$DSH" --profile headless --patch "$PATCH" \
      "Write a complete, working single-file HTML page called index.html: $objective
Rules: one file, inline <style> and <script>, no external anything, no images
or fonts (draw or style everything), must work when opened in a browser with
no build step. Write the file." >/dev/null 2>&1 )
  if [ -f "$dir/index.html" ]; then
    echo "  $(basename "$dir")  $(stat -c%s "$dir/index.html")b  $((SECONDS-t0))s"
  else
    rmdir "$dir" 2>/dev/null; echo "  !! $(basename "$dir") nothing at all"
  fi
done < "$HERE/objectives.txt"
