# Artifacts & Data Map

Where the checkpoints and data live. Distilled from
`claude/plan/thesis-reproduction/04-data-inventory-and-migration.md`, updated to
the **new canonical `saveddata/` layout** being created in parallel.

## Key structural facts

- The real payload does **not** live in the repo. `notebooks/exploratory/dfn/data`
  is a single symlink → `/opt/persistence2/stonedata` (~377 GB on a second
  volume). The repo holds symlinks, not bytes.
- `saveddata/` follows the same "symlink farm" convention: `saveddata/raw/`
  holds the raw rock volumes — the public **Imperial College micro-CT dataset**
  (`scripts/download_imperial_rocks.py` fetches the four reference rocks into
  `saveddata/raw/imperial_college/`). The generated-data migration re-points
  symlinks into `/opt/persistence2/stonedata/` — **zero bytes copied**.
- `notebooks/exploratory/dfn/data/` is the **old** data location and is now
  **disposable** once the symlinks are re-pointed under `saveddata/`. See
  `notebooks/exploratory/dfn/README_STALE.md`.
- Both `saveddata/` and `savedmodels/` are **gitignored**.

## New canonical `saveddata/` layout

```
saveddata/
  raw/                  # raw rock refs (Imperial College micro-CT, uint8 1000^3)
    imperial_college/   #   four reference rocks — scripts/download_imperial_rocks.py
    eleven_sandstones/  #   (legacy extra set, if present)

  gp_training/          # GP porosity-field training data (symlinks)
    gpdata4-129/        #   window 129 (production training set)
    gpdata4-257/        #   window 257 (higher-res variant)

  generated/<stone>/    # KEEP generated families used in analysis (symlinks)
    case_2/   case_3/   case_9/   case_10/
    # (<stone> ∈ bentheimer, doddington, estaillades, ketton)
    # case_10 ⇐ generation-case 5 (FC-129); case_9 ⇐ generation-case 8 (FC-257);
    # case_2/case_3 are the scalar Uncond/Controlled regimes. See REPRODUCE_THESIS.md.

  archive/
    large_volumes/      # large slabs *_case_10_large (symlinks); regenerable from
                        #   checkpoints. NOT backed up inside pore/field_controlled.
                        #   (e.g. estaillades_pfield_gen_case_10_large = 24 GB)

  metrics/              # real .npz (NOT symlinks; small, irreplaceable)
                        #   metrics_<stone>_pfield-gen-*_twophase.npz for cases 9,10,2,3
                        #   + metrics_<stone>_largescale_stride1024_twophase.npz
                        #   + the bentheimer buckley (Buckley-Leverett) npz
```

### Why `metrics/` is the highest-value, lowest-cost artifact

`0005b` writes `metrics_<stone>_<pattern>_twophase.npz` to its `--output` path
(or CWD if omitted); the thesis runs were launched from `scripts/`, so the npz
landed there and were **manually copied** into a `metrics/` dir. The historical
`metrics`, `metrics copy{,2,3}`, `metrics_backup` dirs under `dfn/data/` are
ad-hoc human snapshots — **no script writes to them**. The canonical collection
(`metrics`, newest/most complete) also held metrics for cases whose generated
volumes are **gone from disk** (e.g. case-4/5/8), so the npz set is the *only
surviving record* of several evaluation runs and is **not fully regenerable**.
Treat the consolidated `saveddata/metrics/` as canonical; the
`metrics_backup`-only `*_case-8_buckley.npz` (Buckley-Leverett) were merged in.

## Checkpoint store — `savedmodels/`

```
savedmodels/
  experimental/             # HISTORICAL dated runs (the originals)
    <YYYYMMDD>-dfn-<stone>-<datasource>-porosity-field/checkpoints/last.ckpt
    # e.g. 20260328-dfn-estaillades-gpdata4-129-porosity-field  (129 → 20260328)
    #      20260325-dfn-estaillades-gpdata4-257-porosity-field  (257 → 20260325)
    # date = TRAINING date, NOT derivable from the CLI. Also holds 0009/0009b
    #   unconditional + lysm runs.

  pore/
    production/             # frozen VAE + per-stone scalar-porosity flow ckpts
      converted_vaenet.ckpt           # the 8x-compression VAE used by training & decode
      converted_vaenet_s4_pixnorm*.ckpt, *_s8_pixnorm*.ckpt   # pixnorm/SFT VAE variants
      <stone>_pcond.ckpt              # scalar-porosity production flow ckpts (cases 2/3/4/6)

    field_controlled/       # PRODUCTION field-controlled checkpoints (clean, no date)
      fc129/<stone>.ckpt    #   129-window field model  (use with --generation-case 5)
      fc257/<stone>.ckpt    #   257-window field model  (use with --generation-case 8)
      gpdata4-129/<stone>/  #   PRESERVED GP fields (*_porosity_analysis.npz, *_porosity_field.npy)
      gpdata4-257/<stone>/  #   PRESERVED GP fields
      gp129/  gp257/        #   (GP-field staging dirs)

    vae/                    # additional VAE checkpoints
```

- The `fc129/fc257` checkpoints are the **clean production equivalents** of the
  dated `experimental/...-gpdata4-{129,257}-...` runs — prefer them for
  reproduction.
- **`gpdata2` is dropped** from the canonical `saveddata/gp_training/` layout, but
  the GP fields it represented are **preserved under
  `savedmodels/pore/field_controlled/gpdata4-{129,257}/`**, so the
  field-controlled regime stays reproducible.

## External / disposable

- **`/opt/persistence2/stonedata/`** — the real ~377 GB payload behind every
  `dfn/data` symlink. Survives migration untouched.
- **Imperial College micro-CT dataset** — the raw `.raw` rock volumes; download
  via `scripts/download_imperial_rocks.py`. (The SNOW2 pore-network extractor is
  now vendored into `diffsci2.extra.pore`, so the old `poregen` package is no
  longer needed on `PYTHONPATH`.)
- **`/opt/persistence3/chunk_decode_mmap`** — scratch mmap dir for the large
  `0004e --disk-offload` decodes (must exist with ample free space).
- **`notebooks/exploratory/dfn/data/`** — old location, **disposable** after
  symlink re-point.

See `claude/plan/thesis-reproduction/04-data-inventory-and-migration.md` for the
full size-annotated inventory and the old→new path mapping.
