#!/usr/bin/env bash
# Download the WMH Segmentation Challenge data (DataverseNL doi:10.34894/AECRSD, version 1.0)
# into datasets/wmh/. See README.md.
set -euo pipefail
source "$(dirname "$0")/../lib.sh"

NAME=wmh
OUT=$DATA_ROOT/$NAME
DOI=doi:10.34894/AECRSD
VERSION=1.0
FILES=(uv run --no-project python "$(dirname "$0")/dataverse_files.py")

check_budget $((10 * 10**9))
# The whole release is in scope: training/ and test/ (orig/ + pre/ images and wmh.nii.gz
# for all 170 subjects), additional_annotations/ (observers O3 and O4 on the 60 training
# subjects) and readme.pdf (the challenge website as of December 2022).
# Files are listed via the Dataverse API for the pinned version and fetched by datafile id.
# Only missing or incomplete files are listed, so re-runs resume.
mkdir -p "$OUT/source"
"${FILES[@]}" curl-config "$DOI" "$VERSION" "$OUT/source" > "$OUT/curl.cfg"
if [[ -s $OUT/curl.cfg ]]; then
    curl --parallel --parallel-max 8 -fsSL --retry 5 --create-dirs -C - -K "$OUT/curl.cfg"
fi
rm "$OUT/curl.cfg"
write_manifest "$NAME"
# Check every file against the SHA-1 checksums Dataverse stores for this version.
"${FILES[@]}" verify "$DOI" "$VERSION" "$OUT/source" "$OUT/manifest.sha256"
