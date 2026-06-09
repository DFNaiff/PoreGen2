# `saveddata/` — permanent home for analysis-critical data

This directory gives the analysis-critical data a permanent location so that
`notebooks/exploratory/` can be deleted without losing anything the thesis/paper
depends on.

## Mechanism (read this first)

The big volume directories here are **symlinks** into the real storage volume
`/opt/persistence2/stonedata/`. Re-pointing a symlink copies **zero bytes** — the
real data already lives on `/opt/persistence2`. Every symlink targets the *real*
`/opt/persistence2/stonedata/...` path directly (not the old exploratory symlink),
so deleting `notebooks/exploratory/dfn/data/` later cannot affect anything here.

This matches the pre-existing `saveddata/raw/*` convention (symlinks into
`~/repos/PoreGen/saveddata/raw/`), which is left untouched.

The `metrics/` directory is the one exception: those `.npz` files are **real copied
bytes** (tiny, ~1 MB total) so they survive deletion of the exploratory tree.

## Layout

```
saveddata/
  raw/                  # PRE-EXISTING — symlinks into PoreGen (untouched)
  gp_training/          # GP porosity-field training inputs (symlinks)
    gpdata4-129/        -> /opt/persistence2/stonedata/gpdata4-129   (production training set)
    gpdata4-257/        -> /opt/persistence2/stonedata/gpdata4-257   (257-res variant)
    gpdata2/            -> /opt/persistence2/stonedata/gpdata2       (256-window true fields; kept for thesis field-stat figures — see BACKWARD_COMPAT.md)
  generated/<stone>/    # kept generation cases, per stone (symlinks)
    case_2  -> <stone>_pfield_gen_3_case_2
    case_3  -> <stone>_pfield_gen_3_case_3
    case_9  -> <stone>_pfield_gen_case_9
    case_10 -> <stone>_pfield_gen_case_10
    # <stone> in {bentheimer, doddington, estaillades, ketton}
  archive/large_volumes/    # cold, large dense inference volumes (symlinks)
    <stone>_pfield_gen_case_10_large   # one per stone
  metrics/              # REAL copied .npz (canonical evaluator outputs + buckley)
```

## Old -> new mapping

Source prefix `S = /opt/persistence2/stonedata` (the real targets).
Old exploratory path = `notebooks/exploratory/dfn/data/<name>` (also a symlink into `S`).

| Old (`data/<name>`)                          | Real target                          | New path                                                  |
|----------------------------------------------|--------------------------------------|-----------------------------------------------------------|
| `gpdata4-129`                                | `S/gpdata4-129`                      | `gp_training/gpdata4-129`                                  |
| `gpdata4-257`                                | `S/gpdata4-257`                      | `gp_training/gpdata4-257`                                  |
| `<stone>_pfield_gen_3_case_2`                | `S/<stone>_pfield_gen_3_case_2`     | `generated/<stone>/case_2`                                 |
| `<stone>_pfield_gen_3_case_3`                | `S/<stone>_pfield_gen_3_case_3`     | `generated/<stone>/case_3`                                 |
| `<stone>_pfield_gen_case_9`                  | `S/<stone>_pfield_gen_case_9`       | `generated/<stone>/case_9`                                 |
| `<stone>_pfield_gen_case_10`                 | `S/<stone>_pfield_gen_case_10`      | `generated/<stone>/case_10`                                |
| `<stone>_pfield_gen_case_10_large`           | `S/<stone>_pfield_gen_case_10_large`| `archive/large_volumes/<stone>_pfield_gen_case_10_large`  |
| `metrics/*.npz` (minus case-4/case-6)        | real copy                            | `metrics/*.npz`                                            |
| `metrics_backup/..._case-8_buckley.npz`      | real copy                            | `metrics/metrics_bentheimer_pfield-gen-case-8_buckley.npz`|

## Decisions baked into this migration

- **Kept generation cases: 9, 10, 2, 3 only.** Cases 4 and 6 are EXCLUDED (appendix
  material never used in the paper). The four `case-4` metrics `.npz` were intentionally
  *not* copied; no `case-6` files exist. Cases 5 and 8 survive only as metrics `.npz`
  (their generated-volume dirs are gone and are not reproduced here).
- **`gpdata2` was intentionally NOT migrated.** It is no longer needed; its porosity
  fields are preserved separately in `savedmodels/pore/field_controlled/`. Its real
  bytes on `/opt/persistence2/stonedata/gpdata2` are left in place (not deleted).
- **Duplicate metrics dirs excluded.** Of the five metrics dirs in the exploratory tree
  (`metrics`, `metrics copy`, `metrics copy 2`, `metrics copy 3`, `metrics_backup`),
  only `metrics` is canonical (newest, most complete, carries `largescale_stride1024`).
  It was copied here; the four duplicates were not. The single Buckley–Leverett file
  `metrics_bentheimer_pfield-gen-case-8_buckley.npz` from `metrics_backup` was merged in
  by explicit request.
- **`_xlarge` runs excluded.** `estaillades_..._case_10_xlarge` is an empty/aborted run
  (8 KB stub) and is skipped. `ketton_..._case_10_xlarge` (516 MB, latents-only, no dense
  volume) is also not migrated under the narrowed scope.

## FLAG — `_large` volumes are NOT backed up

The `archive/large_volumes/*_pfield_gen_case_10_large` dirs (bentheimer ~7.1 GB,
doddington ~7.0 GB, **estaillades ~24 GB**, ketton ~7.1 GB) are the large dense
inference volumes. They are **NOT** duplicated in `savedmodels/pore/field_controlled/`
(only the gpdata4 porosity fields are). If `/opt/persistence2/stonedata` is lost, these
volumes are only recoverable by re-running generation from the checkpoint +
`latents/0.latent.pt` recorded in each run's `latent_config.json`. Treat them as the
sole copy.
