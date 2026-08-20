#!/bin/bash
# Run a single GENMO / GEM example (CLI-only, no web demo exists for this tool).
# This mirrors the working smoke test in INSTALL_NOTES.md / run_smoke_tests.sh.
#
# Usage: bash run_genmo_example.sh [path-to-video.mp4] ["text:<prompt>"]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ROOT/envs/genmo/bin/activate"
source "$ROOT/envs/common_env.sh"

# --- Put future test inputs here -------------------------------------------
# Video reference: drop .mp4 files anywhere and pass the path as $1, e.g.
#   bash run_genmo_example.sh /path/to/your/checkpoints/genmo_smoke_input/test_clip.mp4
# Text-only reference: pass a "text:..." string as $2 (or as $1 on its own),
# e.g. "text:a person acting like a monkey"
# -----------------------------------------------------------------------------
VIDEO="${1:-$ROOT/checkpoints/genmo_smoke_input/test_clip.mp4}"
TEXT_PROMPT="${2:-text:a person walking and looking around}"

if [ ! -f "$VIDEO" ]; then
  echo "No input video found at: $VIDEO" >&2
  echo "Usage: bash run_genmo_example.sh <path-to-video.mp4> [\"text:<prompt>\"]" >&2
  exit 1
fi

OUTPUT_ROOT="$ROOT/outputs/genmo"
mkdir -p "$OUTPUT_ROOT"

cd "$ROOT/repos/GENMO"

python scripts/demo/demo_smpl.py \
  --input_list "$VIDEO" "$TEXT_PROMPT" \
  --hmr2_ckpt "$ROOT/checkpoints/genmo/hmr2/epoch=10-step=25000.ckpt" \
  --output_root "$OUTPUT_ROOT" \
  2>&1 | tee "$ROOT/logs/genmo_example.log"

echo "=== Output written under: $OUTPUT_ROOT ==="
