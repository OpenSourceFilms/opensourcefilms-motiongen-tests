# Third-Party Licenses

This repo does not vendor or redistribute any of the three tools tested, their model weights, or any
gated body-model assets — see the README's "What's not here" section. This document records what was
independently verified about each upstream project's licensing, for anyone using `INSTALL_NOTES.md`
to reproduce the evaluation themselves.

OSF's own code in this repo (`launch_kimodo.sh`, `launch_stmc.sh`, `run_genmo_example.sh`,
`run_smoke_tests.sh`, `envs/common_env.sh`, this documentation, and the included
`outputs/kimodo/smoke_test_walk_wave.npz` result file) is MIT-licensed — see `LICENSE`. Nothing below
changes that; it documents the tools being tested, not this repo's own contents.

## Kimodo

- **Upstream:** [github.com/nv-tlabs/kimodo](https://github.com/nv-tlabs/kimodo)
- **Code license:** Apache-2.0.
- **Model checkpoint (Kimodo-SOMA-RP-v1):** distributed separately from the code, under NVIDIA's
  [Open Model License](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1/blob/main/LICENSE), which
  expressly permits commercial use and states NVIDIA does not claim ownership of generated outputs.
- **Commercial-use verdict:** clean — both code and checkpoint license permit commercial use.
- **Dependency:** Kimodo's text encoder (LLM2Vec) wraps `meta-llama/Meta-Llama-3-8B-Instruct`, a
  gated Hugging Face model requiring individual access approval under Meta's own license terms — not
  redistributed here, not evaluated as part of this verdict.

## GENMO / GEM

- **Upstream:** [github.com/NVlabs/GENMO](https://github.com/NVlabs/GENMO) (the project itself has
  since been renamed GEM by its authors; the repository is still named `GENMO`).
- **Code license:** NVIDIA's OneWay Noncommercial License, stated explicitly in the upstream
  repository.
- **Commercial-use verdict:** non-commercial only. Any production use would need a separate
  commercial license from NVIDIA or a swap to a permissively-licensed alternative before commercial
  deployment.
- **Not independently re-verified:** the license terms of the `nvidia/GEM-X` HuggingFace checkpoint
  specifically (distinct from the code license above).

## STMC

- **Upstream:** [github.com/nv-tlabs/stmc](https://github.com/nv-tlabs/stmc)
- **License:** explicitly non-commercial — this covers the code itself, the MTT (Multi-Track
  Timeline) dataset, and the pretrained models, each carrying additional upstream dataset
  restrictions per the repository's own terms.
- **Commercial-use verdict:** non-commercial only, across code, dataset, and pretrained weights.
- **Dependency:** SMPL+H body model (via `mano.is.tue.mpg.de` registration) — separately licensed,
  not redistributed.

## Gated body-model assets (used by GENMO and/or STMC, not redistributed)

- **SMPL-X** — `smpl-x.is.tue.mpg.de`, Max Planck Institute clickthrough license. Individual
  registration required; redistribution not permitted.
- **SMPL+H / MANO** — `mano.is.tue.mpg.de`, same licensing family as SMPL-X. Individual registration
  required; redistribution not permitted.
- **HMR2 checkpoint / ViTPose-H** — third-party checkpoints sourced via a public Google Drive link
  from the GVHMR project (`zju3dv/GVHMR`); license terms not independently re-verified as part of
  this evaluation. Not redistributed here regardless.

## How these verdicts were reached

Verified directly against each upstream project's own repository/model-card LICENSE text (not
inferred from README prose or third-party summaries), cross-checked independently before this repo
was published. Anything not explicitly confirmed above is marked "not independently re-verified"
rather than assumed — treat those as open questions if you're evaluating this for commercial use,
not as settled.
