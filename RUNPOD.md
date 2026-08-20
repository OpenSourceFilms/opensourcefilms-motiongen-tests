# Running on RunPod

This evaluation was run on a RunPod pod: RTX 5090 (Blackwell, sm_120), driver 570.133.20, CUDA 12.8
(nvcc), 16 vCPU, 93GB RAM, 30GB container disk.

## Why RunPod mattered here specifically

RTX 5090/Blackwell support across the PyTorch/CUDA ecosystem was new enough at evaluation time that
none of the three tools' stated install instructions worked as written — every one needed its
suggested PyTorch index (cu118/cu124) overridden to `--index-url
https://download.pytorch.org/whl/cu128`. Access to current-generation GPU hardware, rather than
whatever GPU generation a research repo happened to be validated against, was the whole point of
running this evaluation on RunPod.

## Caches on the persistent volume, not the container disk

`envs/common_env.sh` points `HF_HOME`/`PIP_CACHE_DIR`/`UV_CACHE_DIR`/`TORCH_HOME` at the project
directory. Source it before any install or run step. This matters specifically on RunPod: the
container disk (here, 30GB) is ephemeral and wiped on a pod restart, but a mounted persistent volume
is not — multi-gigabyte model checkpoints and HF caches belong on the volume, not the container FS.

## Exposing the demo ports

Kimodo (`7860`) and STMC (`7862`) each run a local web server that needs a RunPod HTTP proxy port
added (Pod → Edit → expose port) before it's reachable from a browser. Then open the demo via the
RunPod proxy URL — e.g. `https://<pod-id>-7860.proxy.runpod.net` — not `localhost`/`127.0.0.1`/
`0.0.0.0`, none of which resolve outside the pod itself.

STMC's launcher deliberately avoids port `7861`: this pod's container image already runs an internal
`nginx` permanently bound to `7861` (and to `3001`/`7270`/`8001`/`8081`/`9091`), so anything trying to
bind `7861` loses the race — RunPod's dashboard can even show `7861` as "Ready" when nothing you
started is actually listening there. Gradio silently falls back to the next free port if the one
requested is taken, which is why the launcher targets `7862` directly instead.

GENMO is CLI-only — no port to expose.

## GPU note

This was run once against a single pod configuration and GPU (RTX 5090). It has not been re-verified
against other GPU generations or a CPU-only environment — all three tools are diffusion/inference
workloads that assume CUDA is present.
