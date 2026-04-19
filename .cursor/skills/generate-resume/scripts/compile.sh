#!/usr/bin/env bash
# Compile resume-photo.tex → resume-photo.pdf using xelatex
# Usage: from hellojobs/ root: bash .cursor/skills/generate-resume/scripts/compile.sh [tex_file]
#   tex_file defaults to resume/resume-photo.tex

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)/resume"
TEX_FILE="${1:-$RESUME_DIR/resume-photo.tex}"
TEX_NAME="$(basename "$TEX_FILE" .tex)"
OUT_DIR="$(dirname "$TEX_FILE")"

if [[ ! -f "$TEX_FILE" ]]; then
  echo "ERROR: $TEX_FILE not found" >&2
  exit 1
fi

# Check xelatex
if ! command -v xelatex &>/dev/null; then
  echo "ERROR: xelatex not found. Install: sudo apt install texlive-xetex texlive-lang-chinese" >&2
  exit 1
fi

# Check Chinese font
if ! fc-list | grep -qi "Noto Serif CJK SC"; then
  echo "WARNING: Font 'Noto Serif CJK SC' not found."
  echo "  Install: sudo apt install fonts-noto-cjk"
fi

echo "Compiling $TEX_NAME..."
cd "$OUT_DIR"

# Run twice to resolve references
xelatex -interaction=nonstopmode -halt-on-error "$TEX_NAME.tex" > /dev/null
xelatex -interaction=nonstopmode -halt-on-error "$TEX_NAME.tex" > /dev/null

echo "Done → $OUT_DIR/$TEX_NAME.pdf"
