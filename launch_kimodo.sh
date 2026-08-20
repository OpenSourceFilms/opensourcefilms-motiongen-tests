#!/bin/bash
# Launch the Kimodo interactive web demo (viser-based UI).
# Binds 0.0.0.0:7860 by default so RunPod's HTTP proxy can reach it —
# expose/forward port 7860 on the pod to open it from your browser.
#
# Usage: bash launch_kimodo.sh [--model <name>]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ROOT/envs/kimodo/bin/activate"
source "$ROOT/envs/common_env.sh"

# kimodo/demo/config.py reads these env vars (defaults are already 0.0.0.0:7860,
# set explicitly here so the launcher is self-documenting and overridable).
export SERVER_NAME="${SERVER_NAME:-0.0.0.0}"
export SERVER_PORT="${SERVER_PORT:-7860}"

cd "$ROOT/repos/kimodo"

echo "=== Kimodo demo starting on http://$SERVER_NAME:$SERVER_PORT ==="
echo "    (use the RunPod proxy URL for port $SERVER_PORT from your browser, not localhost)"

exec kimodo_demo "$@"
