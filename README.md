# Motion Generation Tool Tests

A **research-evaluation / compatibility-testing** repo, not a production tool. Open Source Films
(OSF) used a RunPod RTX 5090 pod (Blackwell, CUDA 12.8) to install, patch, and run three published
NVIDIA human-motion-generation research projects end to end, and recorded exactly what it took to
get each one working — install order, patched dependency versions, gated-asset requirements, and
upstream bugs hit and fixed along the way.

**Runpod GPU credit made this evaluation possible.** RTX 5090 / Blackwell support in the wider
PyTorch/CUDA ecosystem is still new enough that "pip install and run" routinely fails against a
project's stated requirements — every fix documented in `INSTALL_NOTES.md` (Blackwell PyTorch
reinstalls, a missing-EGL-library fix, a GVHMR upstream-bug workaround) came out of that process.

## What's here

- **`INSTALL_NOTES.md`** — the real, warts-and-all install log for all three tools: exact commands,
  every snag hit, and how each was resolved.
- **`launch_kimodo.sh`**, **`launch_stmc.sh`**, **`run_genmo_example.sh`**, **`run_smoke_tests.sh`**
  — the launcher/test harness scripts OSF wrote around each tool (RunPod-proxy port wiring, env
  setup, smoke-test entry points). These are OSF's own code.
- **`envs/common_env.sh`** — points HF/pip/uv/torch caches at the project directory instead of the
  container filesystem (relevant on RunPod: only the container disk is ephemeral, a mounted
  persistent volume is not).
- **`outputs/kimodo/smoke_test_walk_wave.npz`** — the actual output of a successful Kimodo smoke
  test (150 frames of SOMA-skeleton motion data: joint positions, rotation matrices, root
  trajectory, foot contacts — pure numeric arrays, verified to contain nothing beyond the documented
  motion-data schema).

## What's *not* here, and why

This repo deliberately does not include:
- **The three upstream tool repos** (Kimodo, GENMO/GEM, STMC) — clone them yourself from the links
  below; each keeps its own upstream license (see `THIRD_PARTY_LICENSES.md`).
- **Any model weights or checkpoints** — Kimodo-SOMA-RP-v1, the GEM checkpoint, HMR2/ViTPose, STMC's
  pretrained models. Fetch these from the sources documented in `INSTALL_NOTES.md`.
- **SMPL / SMPL-X / MANO / SMPL+H body-model assets** — these require individual registration at the
  Max Planck Institute's clickthrough-license portals (`smpl-x.is.tue.mpg.de`, `mano.is.tue.mpg.de`)
  and are not ours to redistribute.
- **GENMO or STMC generated output files** — GENMO's output is derived from an identifiable person's
  test footage (see below); STMC's output is derived from an explicitly non-commercial pretrained
  model. Both are described in `INSTALL_NOTES.md` in words instead: what was generated, what pipeline
  stages ran, and what the result looked like.
- **The test source video used for the GENMO run** — a short clip trimmed from OSF's own
  behind-the-scenes production footage that visibly shows a real person's face and likeness. Neither
  that clip nor anything rendered from it is included.
- **Environments, caches, logs, or any machine-specific state** from the pod this was run on.

The result: what's published here is OSF's own harness/documentation, one genuinely clean output
artifact, and a factual account of what worked — not a redistribution of anyone else's restricted
model, weights, or research assets.

## The three tools tested

| Tool | Upstream | What it does | Code license | Model/weights license |
|------|----------|---------------|---------------|------------------------|
| **Kimodo** | [nv-tlabs/kimodo](https://github.com/nv-tlabs/kimodo) | Text/constraint-conditioned motion diffusion | Apache-2.0 | Kimodo-SOMA-RP-v1: NVIDIA Open Model License (commercial use permitted) |
| **GENMO / GEM** | [NVlabs/GENMO](https://github.com/NVlabs/GENMO) | Generalist motion model (video/text/audio → SMPL) | NVIDIA OneWay Noncommercial License | Not independently re-verified beyond the code license — see `THIRD_PARTY_LICENSES.md` |
| **STMC** | [nv-tlabs/stmc](https://github.com/nv-tlabs/stmc) | Timeline-based (Spatio-Temporal Motion Collage) motion generation | Explicitly non-commercial (code, MTT dataset, and pretrained models all carry their own upstream restrictions) | See upstream repo |

Full detail, sources, and how these verdicts were reached: `THIRD_PARTY_LICENSES.md`.

## Results

All three tools were installed from scratch and produced a successful end-to-end generation on this
pod:

- **Kimodo** — text prompt → 150-frame walk-and-wave motion on a 77-joint SOMA skeleton. Output
  included in this repo (`outputs/kimodo/smoke_test_walk_wave.npz`).
- **GENMO / GEM** — video-conditioned motion capture: a short test clip → YOLOv8 person detection →
  ViTPose keypoints → HMR2 features → GEM diffusion → SMPL parameters, rendered as in-camera, global,
  and side-by-side comparison videos. Verified by visual review (the SMPL mesh overlay tracked the
  real person's position and pose correctly) — result described in `INSTALL_NOTES.md`, not
  redistributed (see above).
- **STMC** — timed multi-track text timeline ("walking in a circle" + overlapping "raising both arms
  in the air") → joint positions, SMPL parameters, and rendered skeleton/mesh videos via a
  non-commercial pretrained checkpoint. Verified by visual review — result described in
  `INSTALL_NOTES.md`, not redistributed.

See `INSTALL_NOTES.md` for exact commands, every gated asset each tool required, and the real
upstream bugs hit and fixed along the way (a missing-body-model-file GENMO issue traced to an
un-vendored GVHMR dependency, a headless-EGL rendering fix for STMC, a Blackwell/cu128 PyTorch
reinstall forced by an unpinned transitive dependency).

## Running this yourself

1. Clone the three upstream repos into `repos/` (see links above).
2. Follow `INSTALL_NOTES.md` for each tool's environment setup and gated-asset requirements.
3. `source envs/common_env.sh` before any install/run step.
4. Use `launch_kimodo.sh` / `launch_stmc.sh` / `run_genmo_example.sh` / `run_smoke_tests.sh` as
   documented in the "What's here" section above.

See `RUNPOD.md` for pod-specific GPU/proxy notes.

## Offline publication checks

The repository's [public GitHub Actions workflow](.github/workflows/offline-acceptance.yml)
runs six CPU-only tests. These verify the **already published**
`outputs/kimodo/smoke_test_walk_wave.npz` artifact: seven numeric/bool
fields, expected dtypes and dimensions, consistent 150-frame length, finite
floating-point values, no object/pickle arrays, and 77-joint motion
geometry. The tests also perform `bash -n` syntax checks of the five
published shell scripts without executing model commands.

Only NumPy is installed for the tests. No GPU, Kimodo/GENMO/STMC model,
weights, human subject imagery or RunPod service is required. A passing
result **does not** validate model installation, launchers in a current GPU
environment, kinematic realism, motion quality or any upstream licences.
The captured output artifact and original research verdicts are unchanged.

## Status

Research evaluation / compatibility testing, run once to completion on 2026-07 against a specific
pod configuration. Not maintained as a production tool — treat `INSTALL_NOTES.md` as a point-in-time
account of what worked, not a guarantee against future upstream changes.

---

Runpod-sponsored GPU compute. [Open Source Films](https://opensourcefilms.org).
