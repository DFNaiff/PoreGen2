#!/usr/bin/env python
"""Download the Imperial College micro-CT reference rocks used by DiffSci2.

The four reference rocks (Bentheimer, Doddington sandstones; Estaillades, Ketton
carbonates) are the public **Imperial College pore-scale modelling** 2015
micro-CT dataset:

    https://www.imperial.ac.uk/earth-science/research/research-groups/pore-scale-modelling/micro-ct-images-and-networks/

Each is a 1000^3 uint8 segmented image. The dataset is distributed via Box
shared folders (per-rock and a bulk link), with ``.mhd`` headers next to the raw
volumes. Box shared *folders* have no stable direct-file URL, so fully automated
download generally needs either a browser or a configured ``rclone`` remote;
this script encodes the canonical metadata, checks what is already present, and
guides the rest.

Target layout (matches the paths the pipeline scripts expect):

    saveddata/raw/imperial_college/<Name>_1000c_<voxel>um.raw

Usage:
    python scripts/download_imperial_rocks.py            # status + instructions
    python scripts/download_imperial_rocks.py --rclone box:ICPSC2015   # if you have an rclone remote
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

# name -> (voxel_size_um, box_share_url, expected_raw_filename)
ROCKS = {
    "Bentheimer":  (3.0035,   "https://imperialcollegelondon.box.com/v/iccpsim-bentheimer2015",  "Bentheimer_1000c_3p0035um.raw"),
    "Doddington":  (2.6929,   "https://imperialcollegelondon.box.com/v/iccpsim-doddington2015",  "Doddington_1000c_2p6929um.raw"),
    "Estaillades": (3.31136,  "https://imperialcollegelondon.box.com/v/iccpsim-estaillades2015", "Estaillades_1000c_3p31136um.raw"),
    "Ketton":      (3.00006,  "https://imperialcollegelondon.box.com/v/iccpsim-ketton2015",      "Ketton_1000c_3p00006um.raw"),
}
BULK_URL = "https://imperialcollegelondon.box.com/v/ImagesICPSC2015"
DIMS = 1000
EXPECTED_BYTES = DIMS ** 3  # 1000^3 uint8 = 1,000,000,000 bytes

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DEST = os.path.join(REPO_ROOT, "saveddata", "raw", "imperial_college")


def status(dest: str) -> list[str]:
    """Return the list of rock names still missing from ``dest``."""
    missing = []
    print(f"Target directory: {dest}\n")
    for name, (vox, url, fname) in ROCKS.items():
        path = os.path.join(dest, fname)
        if os.path.exists(path):
            sz = os.path.getsize(path)
            tag = "OK" if sz == EXPECTED_BYTES else f"PRESENT (unexpected size {sz:,} != {EXPECTED_BYTES:,})"
            print(f"  [{tag}] {name:12s} {fname}")
        else:
            missing.append(name)
            print(f"  [ -- ] {name:12s} {fname}   <- {url}")
    return missing


def try_rclone(remote: str, dest: str) -> int:
    """Best-effort bulk copy from a user-configured rclone remote."""
    if subprocess.run(["which", "rclone"], capture_output=True).returncode != 0:
        print("rclone not found on PATH; install it or download manually.", file=sys.stderr)
        return 1
    os.makedirs(dest, exist_ok=True)
    print(f"Running: rclone copy {remote} {dest} --progress")
    return subprocess.run(["rclone", "copy", remote, dest, "--progress"]).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", default=DEFAULT_DEST, help="destination dir (default: saveddata/raw/imperial_college)")
    ap.add_argument("--rclone", metavar="REMOTE:PATH", help="rclone remote to bulk-copy from (e.g. box:ImagesICPSC2015)")
    args = ap.parse_args()

    os.makedirs(args.dest, exist_ok=True)
    if args.rclone:
        rc = try_rclone(args.rclone, args.dest)
        print()
    missing = status(args.dest)

    if not missing:
        print("\nAll four reference rocks are present.")
        return 0

    print("\nManual download (Box shared folders need a browser or rclone):")
    print(f"  - Per-rock links are shown above; or grab everything at once: {BULK_URL}")
    print("  - Each folder has a `.mhd` header + the raw volume; save the raw 1000^3 uint8")
    print(f"    image into {args.dest}/ using the expected filename listed above.")
    print("  - If you keep a configured rclone remote, re-run with --rclone <remote>:<path>.")
    print("\nCitation: Raeini et al. (2017); Imperial College pore-scale modelling group.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
