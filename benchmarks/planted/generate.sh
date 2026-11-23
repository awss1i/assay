#!/usr/bin/env bash
# Write the clean programs of the planted-bug set, one per objective.
#
# It uses the same harness and model as the generated benchmark, so these
# programs are like the ones there. `inject.sh` then plants bugs in a copy.
#
# Usage: generate.sh <output-dir>       (CEREBRAS_API_KEY must be set)
#
# Set OBJECTIVES to another objectives file to write a different set, such as
# the held-out set.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?usage: generate.sh <output-dir>}"
DSH="${DSH:-dsh}"
OBJECTIVES="${OBJECTIVES:-$HERE/objectives.txt}"
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
done < "$OBJECTIVES"
