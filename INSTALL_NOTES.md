# Install Notes

Pod: RTX 5090 (Blackwell, sm_120), driver 570.133.20, CUDA 12.8 (nvcc), 16 vCPU, 93GB RAM, 30GB
container disk (RunPod). Everything below lives under the project root (`$MOTIONGEN_ROOT`, see
`envs/common_env.sh`).

All three repos were cloned with `git clone --depth 1` into `repos/`. All three envs use `uv venv`
(Python 3.10) — **note: `uv venv` does not install `pip` into the venv**; use `uv pip install
--python <venv>/bin/python ...` rather than activating + `pip install`.

Because this is a Blackwell GPU, every repo's suggested PyTorch index (cu118, cu124) was
overridden with `--index-url https://download.pytorch.org/whl/cu128`, installing
**torch 2.11.0+cu128 / torchvision 0.26.0+cu128**, confirmed working via
`torch.cuda.is_available() == True` and `torch.cuda.get_device_name(0) == 'NVIDIA GeForce RTX 5090'`
in all three venvs.

---

## 1. Kimodo — Priority 1

**Repo:** `repos/kimodo` · **Env:** `envs/kimodo`

### What installed
```bash
source envs/common_env.sh
uv venv envs/kimodo --python 3.10
uv pip install --python envs/kimodo/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cu128
cd repos/kimodo
uv pip install --python envs/kimodo/bin/python -e ".[all]"   # includes SOMA body model + kimodo-viser fork
```
This built the `motion_correction` CMake extension without issue and installed `py-soma-x` from
`NVlabs/SOMA-X` and `viser` from the `nv-tlabs/kimodo-viser` fork.

Verified: `import kimodo`, `import motion_correction` both succeed.

### Gated asset — BLOCKING
Kimodo's text encoder (LLM2Vec) wraps **`meta-llama/Meta-Llama-3-8B-Instruct`**, a gated HF model.
An HF token was already cached on this pod. `HfApi.model_info()` with that token succeeds (repo
metadata is public), which is misleading — but an actual file download
(`hf_hub_download(..., 'config.json')`) fails with `GatedRepoError: 403`. **The HF account behind
that token has not been granted access to the gated model itself.**

To fix: log into HF as that account, visit
`https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct`, click "Agree and access repository"
(usually auto-approved instantly for the Meta license).

### Smoke test — SUCCEEDED
Once HF access to the gated Llama-3-8B-Instruct repo was granted, this completed cleanly:
```bash
source envs/common_env.sh
envs/kimodo/bin/kimodo_gen "A person walks forward and waves with their right hand." \
    --model Kimodo-SOMA-RP-v1 --duration 5.0 --output outputs/kimodo/smoke_test_walk_wave
```
Full log in `logs/kimodo_smoke_test.log` (not included in this repo — see "What's not in this repo"
in the README). Output: **`outputs/kimodo/smoke_test_walk_wave.npz`** (955KB, included in this repo
— see README), verified with `numpy.load` — 150 frames on the 77-joint SOMA skeleton, all documented
fields present: `posed_joints` (150,77,3), `global_rot_mats`/`local_rot_mats` (150,77,3,3),
`root_positions`/`smooth_root_pos` (150,3), `foot_contacts` (150,6), `global_root_heading` (150,2).

---

## 2. GENMO / GEM — Priority 2

**Repo:** `repos/GENMO` (upstream renamed the project GEM; repo is still `NVlabs/GENMO`) ·
**Env:** `envs/genmo`

### What installed
```bash
source envs/common_env.sh
uv venv envs/genmo --python 3.10
uv pip install --python envs/genmo/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cu128
cd repos/GENMO
bash scripts/install_env.sh   # patched to point uv pip at envs/genmo/bin/python
```
(README's own quick-start suggests cu124 — overridden to cu128 for Blackwell per above.)

Verified: `import gem` succeeds; `torch.cuda.is_available() == True`.

The main checkpoint `gem_smpl.ckpt` is hosted at `nvidia/GEM-X` on HuggingFace and confirmed
**not gated** — `hf_hub_download` access works with the cached token (unlike Kimodo's Llama
dependency). It auto-downloads on first `demo_smpl.py` run if `--ckpt_path` isn't provided/found.

### Gated assets — obtained and placed
1. **`SMPLX_NEUTRAL.npz`** — requires registering at `https://smpl-x.is.tue.mpg.de/` (Max Planck
   clickthrough license). First attempt used a stripped/body-only export — correct SMPL-X topology
   (10475 verts, 55 joints, valid `J_regressor`/`v_template`/`shapedirs`) but **missing the hand-pose
   fields** (`hands_meanl`, `hands_meanr`) GENMO's `SmplxLite` loader requires at init. Fix: the
   official **SMPL-X v1.1** bundle (`models_smplx_v1_1.zip`, 830MB, from the MPI site), extracting
   `models/smplx/SMPLX_NEUTRAL.npz` from it (full field set incl.
   `hands_meanl`/`hands_meanr`/`hands_componentsl`/`hands_componentsr`/dynamic landmark data) to
   `repos/GENMO/inputs/checkpoints/body_models/smplx/SMPLX_NEUTRAL.npz` (also mirrored to
   `checkpoints/smplx/`). Unofficial HF re-uploads were deliberately avoided both times, for the
   same licensing reason as before. **Not included in this repo — see README.**
2. **HMR2 checkpoint** (`epoch=10-step=25000.ckpt`, 2.71GB) and **ViTPose-H**
   (`vitpose-h-multi-coco.pth`, 2.55GB) — hosted in a public Google Drive folder (linked from
   GVHMR). Direct `gdown` from this environment hit "Too many users have viewed or downloaded this
   file recently" (shared transient quota); resolved via an authenticated browser download of the
   same public files. Verified both as real pytorch zip checkpoints (not HTML login pages) before
   placing: `hmr2/epoch=10-step=25000.ckpt` (root zip entry name matched) → `checkpoints/genmo/hmr2/`;
   ViTPose → `repos/GENMO/inputs/checkpoints/vitpose/` (path hardcoded in
   `scripts/demo/demo_utils.py:114`, no CLI flag for it). **Not included in this repo.**

### Upstream bug hit and fixed: missing body-model asset files
Even with all three gated assets above in place, model instantiation still failed —
`gem/utils/body_model/smplx_lite.py` (and `smpl_augment.py`) load several small `.pt`/`.pth` files
from `gem/utils/body_model/` at import/init time that **are not shipped in the GENMO git repo or the
`nvidia/GEM-X` HF release** (confirmed via GitHub API listing and `HfApi.list_repo_files`): none of
`coco_aug_dict.pth`, `smpl_coco17_J_regressor.pt`, `smplx_verts437.pt`, `smplx2smpl_sparse.pt`,
`smpl_neutral_J_regressor.pt` exist upstream. This matches two known open issues,
[NVlabs/GENMO#17](https://github.com/NVlabs/GENMO/issues/17) and
[#20](https://github.com/NVlabs/GENMO/issues/20) — a commenter on #17 traced it to files that should
have been vendored from **GVHMR** (`zju3dv/GVHMR`), which GENMO's body-model code was adapted from.
Fetched all five files directly from `raw.githubusercontent.com/zju3dv/GVHMR/main/hmr4d/utils/body_model/`
(sizes cross-checked against the GitHub API listing) and placed them in
`repos/GENMO/gem/utils/body_model/` alongside the existing `__init__.py`/`smplx_lite.py`. This is the
canonical upstream source (not the third-party zip attached to the issue) so it needed no separate
trust judgment.

### Smoke test — SUCCEEDED
```bash
source envs/common_env.sh
cd repos/GENMO
../../envs/genmo/bin/python scripts/demo/demo_smpl.py \
    --input_list <video.mp4> "text:a person walking and looking around" \
    --hmr2_ckpt ../../checkpoints/genmo/hmr2/epoch=10-step=25000.ckpt \
    --output_root ../../outputs/genmo
```
Test video: a 6s/1080p/30fps clip trimmed from an internal behind-the-scenes clip from OSF's
production work (a 10s–16s excerpt), re-encoded with `ffmpeg -c:v libx264` to
`checkpoints/genmo_smoke_input/test_clip.mp4` — chosen because no bundled stock/test video in the
environment (gradio/skvideo sample assets) actually contains a person; a frame was pulled and
eyeballed to confirm a visible walking person before running.

Pipeline ran end-to-end: YOLOv8 person detection (180 frames) → ViTPose COCO-17 keypoints → HMR2
features → GEM diffusion inference (235s on RTX 5090) → SMPL param export → in-camera + global +
side-by-side renders. `outputs/genmo/test_clip/smpl_params.pt` (317KB) confirmed to contain
exactly the documented fields: `body_params_global`, `body_params_incam` (both dicts),
`K_fullimg` (480,3,3), `segment_info`. Rendered `1_incam.mp4` frame-checked visually — the SMPL mesh
overlay tracks the real person's position/pose correctly.

**Neither the source clip nor any rendered output from this run is included in this repo** — the
source footage identifiably shows a real person and is not ours to redistribute in that form. See
README for what this means for reproducing the result.

---

## 3. STMC — Priority 3

**Repo:** `repos/stmc` · **Env:** `envs/stmc`

### What installed
```bash
source envs/common_env.sh
uv venv envs/stmc --python 3.10
uv pip install --python envs/stmc/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cu128
cd repos/stmc
uv pip install --python envs/stmc/bin/python setuptools wheel   # needed before requirements.txt
uv pip install --python envs/stmc/bin/python -r requirements.txt   # minus the CLIP line, see below
uv pip install --python envs/stmc/bin/python --reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu128  # requirements.txt pulls in an unpinned torch==2.4.1 (no CUDA/Blackwell support) as a transitive dep — must reinstall cu128 after
uv pip install --python envs/stmc/bin/python --no-build-isolation "clip @ git+https://github.com/openai/CLIP.git"
```

Two install snags, both resolved:
- `openai/CLIP`'s `setup.py` needs `pkg_resources` at build time but doesn't declare it; `uv`'s
  isolated build env doesn't have it. Fix: install it with `--no-build-isolation` (using the main
  venv's already-installed `setuptools`), after first stripping the CLIP line out of
  `requirements.txt` for the main bulk install (`/tmp/stmc_requirements_noclip.txt`), then
  installing CLIP separately.
- `requirements.txt` has no direct torch pin, but a transitive dependency (probably
  `sentence-transformers==2.2.2` or similar) pulls in `torch==2.4.1` from plain PyPI — this
  **predates Blackwell/RTX 5090 support entirely**. Must force-reinstall the cu128 build
  afterward. **Watch for this if requirements.txt is ever re-run.**

Verified: `import torch` (2.11.0+cu128, CUDA True), `import clip`, `import smplx` all succeed.

### Pretrained model — downloaded and verified
```bash
mkdir -p checkpoints/stmc && cd checkpoints/stmc
gdown "https://drive.google.com/uc?id=1CNXnqxGcVHDYzjrfZOlBge7A54OfCt2d" -O pretrained_models.tgz
md5sum pretrained_models.tgz   # 3671e59f678c7dbb2ac3ccb8158875c0 — matches README
cd ../../repos/stmc && tar xfzv ../../checkpoints/stmc/pretrained_models.tgz -C .
```
Extracted to `repos/stmc/pretrained_models/mdm-smpl_clip_smplrifke_humanml3d/` (RUN_DIR), including
`logs/checkpoints/last.ckpt`. (tar prints harmless "Cannot change ownership" warnings — no
permission to chown to the archive's original uid/gid on this filesystem; files still extract
correctly.) **Not included in this repo — STMC's pretrained models/checkpoints are explicitly
non-commercial, see THIRD_PARTY_LICENSES.md.**

### SMPL+H — obtained and merged
`generate.py` unconditionally instantiates an SMPL+H layer at load time
(`smplh = SMPLH(path="deps/smplh", ...)`), regardless of input type — so there is no way to run
even a bare joints-only generation without it. Requires registering at
`https://mano.is.tue.mpg.de/` and downloading `mano_v1_2.zip` and `smplh.tar.xz` ("Extended SMPL+H
model") via an authenticated session (a plain `wget` on the portal URL without that session just
returns the login page HTML).

STMC's README points at TEMOS's `prepare/smplh.sh` / `prepare/merge_smplh_mano.py` to do the actual
merge, but **those scripts aren't included in the STMC repo itself** — pulled them from
`github.com/Mathux/TEMOS` (`prepare/smplh.sh`, `prepare/merge_smplh_mano.py`) and copied into
`repos/stmc/prepare/`.

The merge script depends on `chumpy`, which needs `numpy<1.24` (uses aliases like `np.bool` removed
in later numpy) — incompatible with the rest of STMC's stack (torch 2.11 wants current numpy). Used
a **disposable venv** (`envs/smplh_merge_tmp`) just for this one-time conversion:
```bash
uv venv envs/smplh_merge_tmp --python 3.10
uv pip install --python envs/smplh_merge_tmp/bin/python "numpy<1.24" scipy pip
uv pip install --python envs/smplh_merge_tmp/bin/python --no-build-isolation chumpy

cd repos/stmc/deps/smplh
mkdir tmp && cd tmp
tar xfv ../smplh.tar.xz && unzip ../mano_v1_2.zip
cd ../../../
for gender in male female neutral; do
  ../../envs/smplh_merge_tmp/bin/python prepare/merge_smplh_mano.py \
    --smplh-fn deps/smplh/tmp/$gender/model.npz \
    --mano-left-fn deps/smplh/tmp/mano_v1_2/models/MANO_LEFT.pkl \
    --mano-right-fn deps/smplh/tmp/mano_v1_2/models/MANO_RIGHT.pkl \
    --output-folder deps/smplh/
done
rm -rf deps/smplh/tmp
```
Produces `deps/smplh/SMPLH_{MALE,FEMALE,NEUTRAL}.npz` (~38MB each). The merged files have no chumpy
dependency at load time — `envs/smplh_merge_tmp` isn't needed again after this.

### Smoke test — SUCCEEDED
```bash
source envs/common_env.sh
cd repos/stmc
RUN_DIR=pretrained_models/mdm-smpl_clip_smplrifke_humanml3d
../../envs/stmc/bin/python generate.py run_dir=$RUN_DIR timeline=timelines/walking_circle_raising_arms.txt
```
`timelines/` in the repo already has several example timed-text-timeline files (used
`walking_circle_raising_arms.txt`: "walking in a circle" 0–8s + "raising both arms in the air"
2–5s, on overlapping tracks).

First run got through diffusion + joints rendering but crashed on the SMPL mesh video:
`OSError: Unable to load EGL library` — pyrender/PyOpenGL needs a generic EGL loader for headless
rendering; NVIDIA's vendor lib (`libEGL_nvidia.so.0`) was present but `libegl1` (the generic
`libEGL.so` that dlopens the vendor lib) wasn't installed. Fixed with `apt-get install -y libegl1`
(pulled in `libegl-mesa0`, `libgbm1`, etc. as deps) and re-ran — succeeded completely.

**Output** (`walking_circle_raising_arms_last_timeline_to_motion/`, not included in this repo — STMC
generated output is derived from a non-commercial pretrained model, see THIRD_PARTY_LICENSES.md):
- `walking_circle_raising_arms_timeline_0.npy` — joint positions
- `walking_circle_raising_arms_timeline_0_verts.npy` — mesh vertices (13MB)
- `walking_circle_raising_arms_timeline_0_smpl.npz` — SMPL pose params
- `walking_circle_raising_arms_timeline_0_joints.mp4` — skeleton render
- `walking_circle_raising_arms_timeline_0_smpl.mp4` — SMPL mesh render (4.5MB)

---

## Cross-cutting notes

- **Google Drive quota**: hit once (GENMO's HMR2/ViTPose folder), likely a shared quota on that
  specific public folder (used by many GVHMR-dependent projects), not specific to any one pod/account.
  Worth a periodic retry; typically clears within hours.
- **HF token**: cache a token via `huggingface-cli login` before starting — confirmed valid for
  authentication is not the same as granted-access-to-a-specific-gated-repo; always verify with an
  actual `hf_hub_download` call, not just `model_info()`.
