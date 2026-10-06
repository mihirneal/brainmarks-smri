"""Build the benchmark tables for the WMH Segmentation Challenge from datasets/wmh/source/.

    uv run python scripts/wmh/build_tables.py

See `brainmarks_smri.tables` for the table layout.

- 170 subjects, one session each (session_id '1'): source/<training|test>/<site>[/<scanner>]/<id>/.
  The challenge IDs are unique across sites and cohorts; participant_id is `sub-<id>`.
- Images: FLAIR and T1w, as distributed in orig/ (desc n/a) and bias-field corrected in pre/
  (desc `bias`). `orig/3DT1` is the native 3D T1 (T1w, n/a); `orig/T1` is the same image
  resampled to the FLAIR grid (T1w, `space-FLAIR`; `space-FLAIR_bias` in pre/). The defacing
  masks are modality `mask`: `defaceT1w` (binary, all subjects), and for VU Amsterdam (3D FLAIR)
  also `defaceFLAIR` and `defaceT1w_space-FLAIR` (interpolated, values in [0, 1]; T1_mask is not
  in readme.pdf). The elastix transforms (orig/reg_3DT1_to_FLAIR.txt) are not images.
- Target: wmh.nii.gz, on the FLAIR grid (mask `wmh`; 0 background, 1 WMH, 2 other pathology,
  which the challenge ignores in evaluation). The training subjects also have the masks of
  observers O3 and O4 (`wmh_o3`, `wmh_o4`; additional_annotations/).
- samples.tsv has only what the release gives per subject: site (the folder name) and scanner
  (as named in readme.pdf; the folders only name the three VU Amsterdam scanners). There is no
  age, sex or clinical data, so those template columns are left out.
- Our split: 60/20/20 over all 170 subjects, stratified by scanner, as for the datasets without
  an official split (and like BraTS 2021). `official_split` keeps the challenge cohort
  (training 60, test 110).
- Complete: FLAIR, T1w on the FLAIR grid and the wmh mask (orig/).
"""

import pandas as pd

from brainmarks_smri import tables

NAME = "wmh"
ROOT = tables.dataset_dir(NAME)
SOURCE = ROOT / "source"
# subject folder relative to source/<cohort>/ (minus the id) -> (site, scanner as in readme.pdf)
SCANNERS = {
    "Utrecht": ("Utrecht", "3 T Philips Achieva"),
    "Singapore": ("Singapore", "3 T Siemens TrioTim"),
    "Amsterdam/GE3T": ("Amsterdam", "3 T GE Signa HDxt"),
    "Amsterdam/Philips_VU .PETMR_01.": ("Amsterdam", "3 T Philips Ingenuity"),
    "Amsterdam/GE1T5": ("Amsterdam", "1.5 T GE Signa HDxt"),
}
FILES = {
    "orig/FLAIR.nii.gz": ("FLAIR", None),
    "orig/3DT1.nii.gz": ("T1w", None),
    "orig/T1.nii.gz": ("T1w", "space-FLAIR"),
    "pre/FLAIR.nii.gz": ("FLAIR", "bias"),
    "pre/3DT1.nii.gz": ("T1w", "bias"),
    "pre/T1.nii.gz": ("T1w", "space-FLAIR_bias"),
    "orig/3DT1_mask.nii.gz": ("mask", "defaceT1w"),
    "orig/FLAIR_mask.nii.gz": ("mask", "defaceFLAIR"),
    "orig/T1_mask.nii.gz": ("mask", "defaceT1w_space-FLAIR"),
    "wmh.nii.gz": ("mask", "wmh"),
}
COHORT = {"training": "train", "test": "test"}
CORE = {("FLAIR", "n/a"), ("T1w", "space-FLAIR"), ("mask", "wmh")}


def subjects() -> pd.DataFrame:
    """One row per subject folder: participant_id, cohort, scanner key, folder."""
    rows = []
    for cohort in COHORT:
        for key in SCANNERS:
            if not (SOURCE / cohort / key).exists():  # two Amsterdam scanners are test-only
                continue
            for folder in sorted((SOURCE / cohort / key).iterdir()):
                rows.append((f"sub-{folder.name}", cohort, key, folder))
    s = pd.DataFrame(rows, columns=["participant_id", "cohort", "key", "folder"])
    assert s.participant_id.is_unique, "challenge IDs repeat across sites"
    return s


def images(subj: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in subj.itertuples():
        for name, (modality, desc) in FILES.items():
            path = row.folder / name
            if path.exists():
                rows.append((row.participant_id, "1", modality, desc, str(path.relative_to(ROOT))))
        known = {row.folder / name for name in FILES} | {row.folder / "orig/reg_3DT1_to_FLAIR.txt"}
        assert set(row.folder.rglob("*.*")) <= known, f"unexpected files in {row.folder}"
    for observer in ("o3", "o4"):
        base = SOURCE / "additional_annotations" / f"observer_{observer}" / "training"
        for path in sorted(base.glob("**/result.nii.gz")):
            rows.append((f"sub-{path.parent.name}", "1", "mask", f"wmh_{observer}", str(path.relative_to(ROOT))))
    return pd.DataFrame(rows, columns=tables.IMAGE_COLUMNS)


def samples(subj: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict]]:
    site, scanner = zip(*subj.key.map(SCANNERS))
    s = pd.DataFrame({"participant_id": subj.participant_id, "session_id": "1"})
    s["site"] = site
    s["scanner"] = scanner

    columns = {
        "site": {"Description": "Institute: UMC Utrecht, NUHS Singapore or VU Amsterdam.", "Source": "folder <cohort>/<site>/"},
        "scanner": {
            "Description": "MRI scanner, as named in readme.pdf. VU Amsterdam has three; the Philips Ingenuity and the 1.5 T GE are only in the test set.",
            "Source": "folder <cohort>/<site>/[<scanner>/] (GE3T, Philips_VU .PETMR_01., GE1T5) and readme.pdf",
        },
    }
    return s, columns


def main() -> None:
    subj = subjects()
    img = images(subj)
    smp, columns = samples(subj)
    assert len(smp) == 170 and (subj.cohort == "training").sum() == 60
    assert set(img.participant_id) == set(smp.participant_id)
    observers = img[img.desc.isin(["wmh_o3", "wmh_o4"])].participant_id
    assert set(observers) == set(subj.participant_id[subj.cohort == "training"]) and len(observers) == 120

    participants = smp.set_index("participant_id")
    official = subj.cohort.map(COHORT).set_axis(subj.participant_id)
    strata = participants.scanner
    have = img.assign(desc=img.desc.fillna("n/a")).groupby("participant_id").apply(lambda g: set(zip(g.modality, g.desc)))
    complete = have.map(lambda h: CORE <= h).reindex(participants.index, fill_value=False)
    splits = tables.make_splits(strata, complete, official=official)
    tables.write(NAME, img, smp, columns, splits, summary=["scanner"])


if __name__ == "__main__":
    main()
