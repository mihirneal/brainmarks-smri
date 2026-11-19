"""Microbleed masks for the ADNI T2* GRE images, from the Mayo Clinic reads (MAYOADIRL_MRI_MCH).

    uv run python scripts/adni/microbleeds.py <source dir> <selected_images.tsv>

A read (CHOSEN) gives each definite microbleed as a point in the scan's RAS world coordinates,
which land on the dark dots in the dcm2niix affine. A point is drawn as a ball of POINT_RADIUS_MM
(3 x 3 voxels in plane on the ~0.8 mm grid, one 4 mm slice), so a prediction counts if it reaches
the dot's voxel or its neighbours: the points sit within a voxel of the darkest voxel of the dot.
Possible microbleeds, superficial siderosis and other findings are not labelled; a scan read
without definite microbleeds gets an empty mask.

Writes `<source>/sub-<id>/ses-<..>/anat/sub-<id>_ses-<..>_label-microbleeds_mask.nii.gz` (uint8,
on the T2starw grid) next to each selected T2starw image. Existing masks are kept.
"""

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pyreadr

POINT_RADIUS_MM = 1.5


def definite_points(rda: Path) -> dict[str, np.ndarray]:
    """RAS points [N 3] of the definite microbleeds per read image ID."""
    reads = next(iter(pyreadr.read_r(rda).values()))
    reads = reads[(reads.CHOSEN == 1) & (reads.TYPE == "MCH") & (reads.STATUS == "Definite")]
    points = {}
    for image_id, rows in reads.groupby("LONI_IMG_ID"):
        values = [[float(v) for v in loc.split()[:3]] for loc in rows.RASLOCATIONS]
        points[image_id] = np.array(values).reshape(-1, 3)
        assert np.isfinite(points[image_id]).all(), f"{image_id}: missing coordinates"
    return points


def ball(shape: tuple[int, ...], zooms: np.ndarray, voxels: np.ndarray) -> np.ndarray:
    """Mask of the voxels within POINT_RADIUS_MM of any of `voxels` [N 3]."""
    mask = np.zeros(shape, dtype=bool)
    reach = np.ceil(POINT_RADIUS_MM / zooms).astype(int)
    offsets = np.stack(np.meshgrid(*[np.arange(-r, r + 1) for r in reach], indexing="ij"), -1)
    offsets = offsets.reshape(-1, 3)
    offsets = offsets[np.linalg.norm(offsets * zooms, axis=1) <= POINT_RADIUS_MM]
    for voxel in voxels:
        ball_voxels = voxel + offsets
        ball_voxels = ball_voxels[((ball_voxels >= 0) & (ball_voxels < shape)).all(axis=1)]
        mask[tuple(ball_voxels.T)] = True
    return mask


def write_mask(image_path: Path, points_ras: np.ndarray, out: Path) -> None:
    image = nib.load(image_path)
    ras = np.c_[points_ras, np.ones(len(points_ras))]
    voxels = np.round((np.linalg.inv(image.affine) @ ras.T)[:3].T).astype(int)
    inside = ((voxels >= 0) & (voxels < image.shape[:3])).all(axis=1)
    assert inside.all(), f"{image_path.name}: microbleeds outside the image: {voxels[~inside]}"
    zooms = np.array(image.header.get_zooms()[:3])
    mask = nib.Nifti1Image(ball(image.shape[:3], zooms, voxels).astype(np.uint8), image.affine)
    mask.set_qform(image.affine, code=1)
    partial = out.with_name(out.name.replace(".nii.gz", ".part.nii.gz"))
    mask.to_filename(partial)
    partial.replace(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("selected", type=Path)
    args = parser.parse_args()

    points = definite_points(args.source / "ADNIMERGE2" / "data" / "MAYOADIRL_MRI_MCH.rda")
    selected = pd.read_csv(args.selected, sep="\t", na_values="n/a")
    selected = selected[selected.modality == "T2starw"]
    written = 0
    for row in selected.itertuples():
        anat = args.source / row.participant_id / f"ses-{row.session_id}" / "anat"
        stem = f"{row.participant_id}_ses-{row.session_id}"
        out = anat / f"{stem}_label-microbleeds_mask.nii.gz"
        if not out.exists():
            image_points = points.get(row.image_id, np.zeros((0, 3)))
            write_mask(anat / f"{stem}_T2starw.nii.gz", image_points, out)
            written += 1
    with_microbleeds = selected.image_id.isin(points).sum()
    print(
        f"{len(selected)} T2starw images ({with_microbleeds} with microbleeds), {written} written"
    )


if __name__ == "__main__":
    main()
