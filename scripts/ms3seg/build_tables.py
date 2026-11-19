"""Build the benchmark tables for MS3SEG (figshare, version 6) from datasets/ms3seg/source/.

    uv run python scripts/ms3seg/build_tables.py

Table layout: `README_hf.md`.

- 100 multiple sclerosis patients (sub-001 .. sub-100, the release's patient numbers), one
  session each (session_id '1'), all from one center (Golgasht Medical Imaging Center, Tabriz)
  on one 1.5 T Toshiba Vantage Elan.
- Images: the 2D axial FLAIR and its MS lesion (abWMH) mask, on the same grid (0/255).
- Age and sex from the FLAIR sidecars. The lesion volume and count (26-connected) are computed
  from the mask.
- No official split. Dev/test 50/50 by participant, stratified by lesion volume tertile.
"""

import json

import nibabel as nib
import numpy as np
import pandas as pd
from scipy import ndimage

from brainmarks_smri.utils import tables

NAME = "ms3seg"
ROOT = tables.dataset_dir(NAME)
SOURCE = ROOT / "source"
N_PATIENTS = 100


def images() -> pd.DataFrame:
    rows = []
    for flair in sorted(SOURCE.glob("MS_100_patient_nifti/*/*_FLAIR.nii.gz")):
        patient = flair.parent.name
        mask = SOURCE / "MS_100_patient_masks" / "abWMH_Masks" / patient
        mask = mask / f"{patient}_abWMH_Mask.nii.gz"
        for modality, desc, path in [("FLAIR", None, flair), ("mask", "lesion", mask)]:
            rows.append((f"sub-{patient}", "1", modality, desc, str(path.relative_to(ROOT))))
    return pd.DataFrame(rows, columns=tables.IMAGE_COLUMNS)


def lesions(flair_path: str, mask_path: str) -> tuple[float, int]:
    """Lesion volume (ml) and count (26-connected components), after checking the mask grid."""
    flair = nib.load(ROOT / flair_path)
    mask_image = nib.load(ROOT / mask_path)
    assert mask_image.shape == flair.shape, f"{mask_path}: not on the FLAIR grid"
    assert np.allclose(mask_image.affine, flair.affine, atol=1e-3), f"{mask_path}: affine"
    values = np.asarray(mask_image.dataobj)
    assert set(np.unique(values).round()) <= {0, 255}, f"{mask_path}: labels"
    mask = values > 0
    voxel_ml = float(np.prod(flair.header.get_zooms()[:3])) / 1000
    count = ndimage.label(mask, np.ones((3, 3, 3), dtype=bool))[1]
    return float(mask.sum()) * voxel_ml, int(count)


def samples(img: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict]]:
    paths = img.pivot(index="participant_id", columns="modality", values="path")
    s = pd.DataFrame({"participant_id": paths.index, "session_id": "1"})
    sidecars = [
        json.loads((ROOT / path.replace(".nii.gz", ".json")).read_text()) for path in paths.FLAIR
    ]
    ages = [sidecar["PatientAge"] for sidecar in sidecars]
    assert all(age.endswith("Y") for age in ages), "ages not in years"
    s["age"] = [int(age.removesuffix("Y")) for age in ages]
    s["sex"] = [sidecar["PatientSex"] for sidecar in sidecars]
    s["site"] = pd.NA
    volumes, counts = zip(*(lesions(f, m) for f, m in zip(paths.FLAIR, paths["mask"])))
    s["ms_lesion_volume"] = np.round(volumes, 3)
    s["ms_lesion_count"] = counts
    columns = {
        "site": {"Description": "Single center (Golgasht Medical Imaging Center), so n/a."},
        "ms_lesion_volume": {
            "Description": "Volume of the MS lesion mask.",
            "Units": "ml",
            "Source": "abWMH mask",
        },
        "ms_lesion_count": {
            "Description": "Number of MS lesions: 26-connected components of the mask.",
            "Source": "abWMH mask",
        },
    }
    return s, columns


def main() -> None:
    img = images()
    smp, columns = samples(img)
    assert len(smp) == N_PATIENTS and (smp.ms_lesion_count > 0).all()

    participants = smp.set_index("participant_id")
    strata = pd.qcut(participants.ms_lesion_volume, 3, labels=["low", "mid", "high"])
    splits = tables.make_splits(strata)
    tables.write(NAME, img, smp, columns, splits)
    print(tables.summary_table(smp, splits, ["ms_lesion_volume", "ms_lesion_count"]))


if __name__ == "__main__":
    main()
