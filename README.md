# DiffSci2

DiffSci2 is the research codebase behind the DSc thesis **"Large-Scale Porous
Media Reconstruction Through Generative Diffusion Models"** (Danilo Naiff). It
implements a 3D **latent diffusion** pipeline that reconstructs binarized
micro-CT rock volumes, conditions generation on a spatially varying **Gaussian-
process porosity field**, and scales inference (via chunked VAE decode and
spatial/domain parallelism) to volumes far larger than any training subvolume
(1024³ slabs and 1024²×4096 "large" slabs). Generated rocks are validated
physically through pore-network modeling (PNM): porosity, absolute and relative
permeability, capillary pressure, two-point correlation / pore-size
distribution, and an oil-water Buckley-Leverett flow analysis.

The installable Python package is **`diffsci2`** (`setup.py`, `name='diffsci2'`).
The four reference rocks are the Imperial College set: **Bentheimer,
Doddington, Estaillades, Ketton** (1000³ uint8 `.raw`), supplied by the sibling
repo **PoreGen**.

> **Note on this README.** It replaces the old cookiecutter boilerplate (which
> referenced a nonexistent `diffsci` package and `make data`/`make train`
> targets). For the authoritative, verified pipeline study see
> `claude/plan/thesis-reproduction/` and the distilled docs in `docs/`.

---

## End-to-end pipeline

```
RAW rock volumes (Imperial College: Bentheimer, Doddington, Estaillades, Ketton)
   |  (sibling repo ~/repos/PoreGen/saveddata/raw/imperial_college/*.raw, uint8 1000^3)
   v
GP porosity-field training data  ──  gpdata4-129 (window 129) / gpdata4-257 (window 257)
   |     (per-stone *_porosity_field_full.npy, 1000^3 float64; + *_porosity_analysis.npz Matern params)
   v
[TRAIN]  scripts/0003-porosity-field-training.py   →  checkpoint
   |        (per stone × {129 crop64, 257 crop128}; frozen VAE = savedmodels/pore/production/converted_vaenet.ckpt)
   v
[GENERATE]  scripts/0004e-porosity-field-generator.py   (two stages)
   |   Stage 1  --mode latent   (torchrun, multi-GPU, spatial-parallel) → latents/*.latent.pt
   |   Stage 2  --mode decode   (1 GPU, chunked, optional disk-offload)  → data/*.npy (binarized)
   v
synthetic volumes  (per case dir; 1280^3 cubes → crop to 1024^3, or large 1280×1280×4352 slabs)
   |
   ├─[DIVERSITY] scripts/0010-diversity-calculation.py        → strided per-block porosity/permeability fields
   ├─[METRICS]   scripts/0005b-…-new-metrics-evaluator.py     → metrics_<stone>_<pattern>_twophase.npz
   ├─[LARGE]     scripts/0005d-…-large-subvol.py              → metrics_<stone>_largescale_stride1024_*.npz
   ├─[PNM-LARGE] scripts/0005-…-large-pnm.py                  → whole-slab 0.network.npz (consumed by 0011)
   └─[FLOW]      scripts/0011-oil-water-flow.py               → oilwater_results.npz (Corey + Buckley-Leverett)
   |
   v
[FIGURES]  notebooks/exploratory/dfn/tolatex/scripts/generate_*.py (+ a few notebooks)  →  thesis Figures/
```

**Canonical thesis spine:** `0002 → 0003 → 0004e → {0005, 0005b, 0005d-large-subvol,
0010} → 0005-large-pnm → 0011`. The `0004 / 0004c / 0004d` generators are
*superseded* by `0004e`. See `docs/SCRIPTS_CATALOG.md` for the full
canonical-vs-superseded verdict — the numbered prefix is a **lineage, not a
stable API**.

---

## Repository map

| Zone | Tracked | What it is |
|---|---|---|
| `diffsci2/` | yes | The installable library: `nets/` (PUNetG U-Net, VAENet, local-attention NATTEN backbone), `models/karras/` (EDM-sigma-space flow `SIModule`/`EDMModule` diffusion core), `models/vae/` (`VAEModule`), `vaesft/` (VAE supervised fine-tune through a frozen reward), `data/` (subvolume datasets + cube-symmetry aug), `distributed/` (spatial/domain parallelism for PUNetG inference), `extra/` (chunked decode, Matérn GP fields, `extra/pore/` PNM physics). |
| `scripts/` | yes | The numbered `0001`–`0012` experiment lineage (train → generate → evaluate → physics). Many superseded variants — see `docs/SCRIPTS_CATALOG.md`. |
| `pipelines/vae/` | yes | Productionized VAE-SFT pipeline (train/eval/smoke). Depends INTO the AI-research playground (see below). |
| `tests/` | yes | Unit tests + `tests/chunk_decode_encode/` correctness suite. |
| `docs/` | yes | The distilled docs (this `.md` set) alongside a legacy Sphinx stub. |
| `claude/` | no (gitignored) | Agent-facing plans/reports, including `claude/plan/thesis-reproduction/` (the verified source-of-truth for the thesis pipeline). |
| `notebooks/exploratory/dfn/` | no | Thesis analysis notebooks + `tolatex/` figure scripts. **Pre-migration / unmaintained** — see `notebooks/exploratory/dfn/README_STALE.md`. |
| `notebooks/exploratory/dfnai/` | no | "AI-as-researchers" subprojects (poreregressor, vaeporesft, …) — being promoted to a top-level gitignored `aiplayground/` (report 05). |
| `notebooks/exploratory/lysm/` | no | Léo's multi-front workspace (self-documenting `context/` + `docs/`). |
| `saveddata/` | no (gitignored) | Data symlink farm (`raw/` → PoreGen; the new canonical `gp_training/`, `generated/`, `metrics/`, `archive/` layout — see `docs/ARTIFACTS_AND_DATA.md`). |
| `savedmodels/` | no (gitignored) | Checkpoint store: `experimental/` (historical dated runs), `pore/production/` (frozen VAEs + per-stone scalar ckpts), `pore/field_controlled/` (production field-controlled ckpts + preserved GP fields). |

---

## Environment

- **Conda env:** `ddpm_env` (Linux / Ubuntu; remote dev via VSCode Remote SSH is typical).
- **Install:** the package is `diffsci2`; install editable from repo root (`pip install -e .`) so `import diffsci2` resolves regardless of CWD.
- **GPUs:** scripts take literal physical GPU indices (no `CUDA_VISIBLE_DEVICES`); e.g. `--devices 1,2,3,4,5,6` binds GPUs 1–6. Multi-GPU generation uses `torchrun` for spatial-parallel latent sampling. **Avoid GPU 7 unless explicitly told otherwise.** Long jobs should run inside `screen`.
- **External coupling:** the sibling repo **PoreGen** (`~/repos/PoreGen`) supplies the raw `.raw` volumes and the SNOW2 pore-network extractor (`poregen.features.snow2`); it must be on `PYTHONPATH` whenever SNOW2 actually runs. OpenPNM is the underlying PNM flow engine.
- **No seeding.** None of the pipeline scripts seed torch/numpy/Lightning, so every run is non-deterministic.

---

## Where to look next

- `docs/SCRIPTS_CATALOG.md` — every numbered script with status (canonical / superseded / dead).
- `docs/REPRODUCE_THESIS.md` — the corrected, runnable train → generate → evaluate → physics runbook.
- `docs/ARTIFACTS_AND_DATA.md` — where checkpoints and data live (`savedmodels/`, `saveddata/`, the `/opt/persistence2/stonedata` symlink farm).
- `claude/plan/thesis-reproduction/00-overview.md` … `06-…` — the seven verified study reports these docs distill (the agent-facing source of truth).
