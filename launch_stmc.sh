#!/bin/bash
# Launch the STMC Gradio timeline-to-motion demo.
# Forces SHARE=False in app_config.py (no public gradio.live share link) and
# binds 0.0.0.0:7862 via GRADIO_SERVER_NAME/PORT so RunPod's HTTP proxy can
# reach it — expose/forward port 7862 on the pod to open it from your browser.
#
# NOTE: port 7861 is NOT used here — this container's pod image already runs
# its own nginx bound to 7861 (and to 3001/7270/8001/8081/9091), so any app
# trying to bind 7861 will lose the race and Gradio silently falls back to
# the next free port. 7862 avoids that collision.
#
# Usage: bash launch_stmc.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ROOT/envs/stmc/bin/activate"
source "$ROOT/envs/common_env.sh"

cd "$ROOT/repos/stmc"

# Disable the public Gradio share link (idempotent — only flips True -> False).
sed -i 's/^SHARE = True/SHARE = False/' app_config.py

export GRADIO_SERVER_NAME="${GRADIO_SERVER_NAME:-0.0.0.0}"
export GRADIO_SERVER_PORT="${GRADIO_SERVER_PORT:-7862}"

echo "=== STMC demo starting on http://$GRADIO_SERVER_NAME:$GRADIO_SERVER_PORT (share link disabled) ==="
echo "    (use the RunPod proxy URL for port $GRADIO_SERVER_PORT from your browser, not localhost)"

exec python app.py "$@"
