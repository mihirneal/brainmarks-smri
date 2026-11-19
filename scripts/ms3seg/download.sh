#!/usr/bin/env bash
# Download MS3SEG (figshare 10.6084/m9.figshare.30393475, version 6) into datasets/ms3seg/.
# See README.md. Needs 7-Zip (`7zz`) for the RAR archives.
set -euo pipefail
source "$(dirname "$0")/../lib.sh"

NAME=ms3seg
OUT=$DATA_ROOT/$NAME
# figshare file ID, name and md5 (version 6, 2026-06-21): the NIfTI images (all sequences, in
# three RAR volumes) and the masks.
FILES=(
    "61900798 MS_100_patient_nifti.part1.rar c720bddd56af0c73f77ccb816fc4f343"
    "61901377 MS_100_patient_nifti.part2.rar 4b14e215ece646747bad77beec821a6c"
    "61901674 MS_100_patient_nifti.part3.rar a2b566ebf66cd7826a446ae320fb7413"
    "65733546 MS_100_patient_masks.rar fb0b4ab3980851db957f9ca8ab350bef"
)

command -v 7zz > /dev/null || die "7zz (7-Zip) not found: install it to extract the RAR archives"
check_budget $((6 * 10**9))
if [[ ! -d "$OUT/source" ]]; then
    mkdir -p "$OUT/archives"
    for file in "${FILES[@]}"; do
        read -r id name md5 <<< "$file"
        if ! [[ -f "$OUT/archives/$name" ]] || ! echo "$md5  $OUT/archives/$name" | md5sum -c --quiet; then
            curl -fL -C - --retry 5 -sS -o "$OUT/archives/$name" \
                "https://ndownloader.figshare.com/files/$id"
            echo "$md5  $OUT/archives/$name" | md5sum -c --quiet || die "$name: checksum mismatch"
        fi
    done
    rm -rf "$OUT/.tmp-source"
    # Only what the task uses: the axial FLAIR with its sidecar and the MS lesion (abWMH) mask.
    7zz x -bd -y "$OUT/archives/MS_100_patient_nifti.part1.rar" -o"$OUT/.tmp-source" \
        -ir!'*_FLAIR.nii.gz' -ir!'*_FLAIR.json' > /dev/null
    7zz x -bd -y "$OUT/archives/MS_100_patient_masks.rar" -o"$OUT/.tmp-source" \
        -ir!'*_abWMH_Mask.nii.gz' > /dev/null
    mv "$OUT/.tmp-source" "$OUT/source"
    rm -r "$OUT/archives"
fi
write_manifest "$NAME"
