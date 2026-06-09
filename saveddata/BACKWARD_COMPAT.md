# Backward compatibility — thesis figure scripts vs the data migration

## The coupling

Every thesis figure script in
`notebooks/exploratory/dfn/tolatex/scripts/generate_*.py` **hardcodes**:

```python
DATA_DIR    = '/home/ubuntu/repos/DiffSci2/notebooks/exploratory/dfn/data/'
METRICS_DIR = '/home/ubuntu/repos/DiffSci2/notebooks/exploratory/dfn/data/metrics'
```

and reads, relative to those:

- generated case volumes — `DATA_DIR/<stone>{suffix}/data/*.npy`
- true porosity fields — `DATA_DIR/gpdata2/<stone>/..._porosity_field_full.npy`
  (256-window, cases 1–4) and `DATA_DIR/gpdata4-129|257/...` (case 5 / FC runs)
- evaluation metrics — `METRICS_DIR/metrics_<stone>_..._twophase.npz`
- two-phase flow — `oilwater_results.npz` inside each `_large` dir
- case table — `../casename.txt`

## Why nothing is broken right now

The migration to `saveddata/` was **purely additive** — no file under
`notebooks/exploratory/dfn/data/` was moved or deleted. `dfn/data` is itself a
single symlink to `/opt/persistence2/stonedata/`, and that symlink is intact, so
every hardcoded path above still resolves. **The thesis scripts run unchanged.**

`saveddata/` is a *parallel, clean* view of the same real data (symlinks to the
same `/opt/persistence2/stonedata` targets) plus a **real copy** of the metrics
`.npz` (so the metrics survive even if the exploratory tree is deleted).

## gpdata2 — kept for compatibility

Although gpdata2 was initially slated to be dropped, `generate_field_statistics_all_cases.py`
(and the older `generate_field_statistics_figures.py`) read it as the 256-window
true field for cases 1–4 — **cases 2 and 3 are in the paper**. So gpdata2 is kept
as a (zero-byte) symlink at `saveddata/gp_training/gpdata2`. Its porosity fields
are also preserved in `savedmodels/pore/field_controlled/`. It can be slimmed
later only if those field-statistics figures are regenerated from a different
reference or dropped.

## When you eventually "throw away" `notebooks/exploratory/`

To delete the exploratory tree **without breaking the thesis figure scripts**,
do exactly one of:

1. **Keep the one compat symlink** (recommended, zero cost): preserve
   `notebooks/exploratory/dfn/data -> /opt/persistence2/stonedata` even after
   deleting everything else in `notebooks/exploratory/`. Because that single
   symlink is the only thing the hardcoded `DATA_DIR`/`METRICS_DIR` paths need,
   the scripts keep working. (Note: the `metrics/` real copy now also lives in
   `saveddata/metrics/`, so metrics are double-covered.)

2. **Repoint the scripts**: change `DATA_DIR`/`METRICS_DIR` in each
   `tolatex/scripts/generate_*.py` to `saveddata/` equivalents
   (`saveddata/generated/<stone>/...`, `saveddata/gp_training/...`,
   `saveddata/metrics`). This decouples the thesis from the exploratory tree
   entirely but requires editing ~12 scripts and adjusting the `<stone>{suffix}`
   → `case_N` directory-name mapping.

Until you decide to regenerate/update thesis figures, **option 1 is the safe
default** and requires no edits.

## Scripts with hardcoded paths (for option 2, if ever taken)

`generate_case_comparison_figures.py`, `generate_2304_figures.py`,
`generate_diversity_boxplots.py`, `generate_field_statistics_figures.py`,
`generate_field_statistics_all_cases.py`, `generate_field_slices.py`,
`generate_largescale_subvolume_figures.py`, `generate_individual_figs.py`,
`generate_visual_comparison.py`, `generate_oilwater_figures.py` (takes
`--results` path), plus the shared `casename.txt` loader. Each defines
`DATA_DIR`/`METRICS_DIR` near the top of the file.
