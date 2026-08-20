#!/bin/bash
# Run one (or all) of the motion-generation smoke tests.
# Usage: bash run_smoke_tests.sh [kimodo|genmo|stmc|all]
#
# See INSTALL_NOTES.md for the gated assets each tool needs before its
# smoke test can succeed. This script does not attempt to fetch those.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/envs/common_env.sh"

run_kimodo() {
  echo "=== Kimodo smoke test ==="
  mkdir -p "$ROOT/outputs/kimodo"
  "$ROOT/envs/kimodo/bin/kimodo_gen" \
    "A person walks forward and waves with their right hand." \
    --model Kimodo-SOMA-RP-v1 \
    --duration 5.0 \
    --output "$ROOT/outputs/kimodo/smoke_test_walk_wave" \
    2>&1 | tee "$ROOT/logs/kimodo_smoke_test.log"
}

run_genmo() {
  echo "=== GENMO / GEM smoke test ==="
  echo "Requires: SMPLX_NEUTRAL.npz in repos/GENMO/inputs/checkpoints/body_models/smplx/"
  echo "          HMR2 ckpt in checkpoints/genmo/hmr2/epoch=10-step=25000.ckpt"
  echo "          A test video: pass its path as \$1 to this function, or edit this script"
  local video="${1:-}"
  if [ -z "$video" ]; then
    echo "Usage: bash run_smoke_tests.sh genmo <path-to-video.mp4>" >&2
    return 1
  fi
  mkdir -p "$ROOT/outputs/genmo"
  cd "$ROOT/repos/GENMO"
  "$ROOT/envs/genmo/bin/python" scripts/demo/demo_smpl.py \
    --input_list "$video" "text:a person acting like a monkey" \
    --hmr2_ckpt "$ROOT/checkpoints/genmo/hmr2/epoch=10-step=25000.ckpt" \
    --output_root "$ROOT/outputs/genmo" \
    2>&1 | tee "$ROOT/logs/genmo_smoke_test.log"
}

run_stmc() {
  echo "=== STMC smoke test ==="
  echo "Requires: deps/smplh/{SMPLH_NEUTRAL,SMPLH_MALE,SMPLH_FEMALE}.npz in repos/stmc/deps/smplh/"
  mkdir -p "$ROOT/outputs/stmc"
  cd "$ROOT/repos/stmc"
  RUN_DIR="pretrained_models/mdm-smpl_clip_smplrifke_humanml3d"
  "$ROOT/envs/stmc/bin/python" generate.py \
    run_dir="$RUN_DIR" \
    timeline=timelines/walking_circle_raising_arms.txt \
    2>&1 | tee "$ROOT/logs/stmc_smoke_test.log"
  echo "Outputs land in repos/stmc/$RUN_DIR/generations/ — copy to outputs/stmc/ if you want them there:"
  echo "  cp -r $ROOT/repos/stmc/$RUN_DIR/generations/* $ROOT/outputs/stmc/"
}

case "${1:-all}" in
  kimodo) run_kimodo ;;
  genmo) run_genmo "${2:-}" ;;
  stmc) run_stmc ;;
  all)
    run_kimodo
    echo
    echo "Skipping genmo (needs a video path) and stmc unless assets are in place — run them individually."
    ;;
  *)
    echo "Usage: $0 [kimodo|genmo <video.mp4>|stmc|all]" >&2
    exit 1
    ;;
esac
