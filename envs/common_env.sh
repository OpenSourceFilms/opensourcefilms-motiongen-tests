#!/bin/bash
# Points caches at this project directory instead of the container filesystem,
# so nothing gets lost on a container restart (relevant on RunPod, where only
# the container disk is ephemeral — a mounted persistent volume is not).
#
# Resolves its own root dynamically so this works regardless of clone location
# (`envs/` is always one level below the project root).
MOTIONGEN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export MOTIONGEN_ROOT

export HF_HOME=$MOTIONGEN_ROOT/caches/huggingface
export HUGGINGFACE_HUB_CACHE=$HF_HOME/hub
export PIP_CACHE_DIR=$MOTIONGEN_ROOT/caches/pip
export UV_CACHE_DIR=$MOTIONGEN_ROOT/caches/uv
export UV_PYTHON_INSTALL_DIR=$MOTIONGEN_ROOT/caches/uv/python
export TORCH_HOME=$MOTIONGEN_ROOT/caches/torch
export XDG_CACHE_HOME=$MOTIONGEN_ROOT/caches
