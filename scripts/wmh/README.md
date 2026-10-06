# WMH 2017

The MICCAI 2017 White Matter Hyperintensity (WMH) Segmentation Challenge: 170 subjects from three hospitals (UMC Utrecht, NUHS Singapore, VU Amsterdam) on five scanners, each with a 3D T1 and a FLAIR image and a manual WMH segmentation on the FLAIR. We use it for WMH segmentation. The test set, kept secret during the challenge (2017–2022), was released with its labels in December 2022.

- **Homepage:** <https://wmh.isi.uu.nl/> (archived in `readme.pdf`; the site was unreachable on 2026-10-03)
- **Source:** DataverseNL [Data of the WMH Segmentation Challenge](https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/AECRSD&version=1.0). The file list of the pinned version comes from the Dataverse native API, and curl fetches each file by datafile id (`/api/access/datafile/<id>`). Every file is then checked against the SHA-1 that Dataverse stores for it.
- **Version:** 1.0 (released 2022-12-21), the only version as of 2026-10-03.
- **DOI:** [10.34894/AECRSD](https://doi.org/10.34894/AECRSD)
- **License:** CC BY-NC 4.0 (the DataverseNL release). `readme.pdf` still carries the challenge's original terms of participation (registered teams only, no redistribution), from before the public release.
- **Citation:** Kuijf, H. J., et al. (2019). Standardized Assessment of Automatic Segmentation of White Matter Hyperintensities and Results of the WMH Segmentation Challenge. *IEEE Transactions on Medical Imaging*, 38(11), 2556–2568. [doi:10.1109/TMI.2019.2905770](https://doi.org/10.1109/TMI.2019.2905770). Data: Kuijf, H., Biesbroek, M., de Bresser, J., Heinen, R., Chen, C., van der Flier, W., Barkhof, F., Viergever, M., & Biessels, G. J. (2022). Data of the White Matter Hyperintensity (WMH) Segmentation Challenge. DataverseNL. [doi:10.34894/AECRSD](https://doi.org/10.34894/AECRSD).
- **Code:** [`scripts/wmh/`](https://github.com/MedARC-AI/brainmarks-smri/tree/main/scripts/wmh) re-downloads `source/` and rebuilds `tables/`. The challenge's evaluation code is at [hjkuijf/wmhchallenge](https://github.com/hjkuijf/wmhchallenge).

## Samples

One sample per subject (170, one session each). Split 60/20/20 over all subjects, stratified by scanner, as for the datasets without an official split. `official_split` keeps the challenge cohort (training 60, test 110; the test set has two scanners not in training). Complete = FLAIR, T1w on the FLAIR grid and the WMH mask (all 170). The release has no age, sex or clinical data, so `samples.tsv` has no such columns.

| split | participants | complete | sites | scanner |
|---|---|---|---|---|
| train | 102 | 102 | 3 | 1.5 T GE Signa HDxt 6 / 3 T GE Signa HDxt 30 / 3 T Philips Achieva 30 / 3 T Philips Ingenuity 6 / 3 T Siemens TrioTim 30 |
| val | 34 | 34 | 3 | 1.5 T GE Signa HDxt 2 / 3 T GE Signa HDxt 10 / 3 T Philips Achieva 10 / 3 T Philips Ingenuity 2 / 3 T Siemens TrioTim 10 |
| test | 34 | 34 | 3 | 1.5 T GE Signa HDxt 2 / 3 T GE Signa HDxt 10 / 3 T Philips Achieva 10 / 3 T Philips Ingenuity 2 / 3 T Siemens TrioTim 10 |
| total | 170 | 170 | 3 | 1.5 T GE Signa HDxt 10 / 3 T GE Signa HDxt 50 / 3 T Philips Achieva 50 / 3 T Philips Ingenuity 10 / 3 T Siemens TrioTim 50 |

## Contents

`source/`: the complete release (1,791 files, 8.8 GB):

- `training/` (60) and `test/` (110), as `<site>/[<scanner>/]<id>/`: Utrecht, Singapore and `Amsterdam/GE3T` in both, `Amsterdam/Philips_VU .PETMR_01.` (Philips Ingenuity) and `Amsterdam/GE1T5` (1.5 T GE) in test only. Subject IDs are unique across sites and cohorts. Each subject has:
  - `orig/3DT1.nii.gz` (defaced 3D T1, ~1 mm isotropic) and `orig/3DT1_mask.nii.gz` (the defacing mask).
  - `orig/FLAIR.nii.gz`: the 2D FLAIR (3 mm slices; the Amsterdam 3D FLAIRs were reoriented transversal and resampled to 3 mm by the organizers). This is the reference space for the annotations and the evaluation.
  - `orig/T1.nii.gz`: the 3D T1 registered (elastix 4.8, rigid) and resampled to the FLAIR grid, with the transform in `orig/reg_3DT1_to_FLAIR.txt`. Amsterdam subjects also have `orig/FLAIR_mask.nii.gz` and `orig/T1_mask.nii.gz` (defacing masks on the FLAIR grid).
  - `pre/3DT1.nii.gz`, `pre/FLAIR.nii.gz`, `pre/T1.nii.gz`: the same images bias-field corrected with SPM12 r6685.
  - `wmh.nii.gz`: the reference standard on the FLAIR grid: 0 background, 1 WMH, 2 other pathology. Observer O1's STRIVE-based delineations after peer review by O2.
- `additional_annotations/observer_o3/` and `observer_o4/`: `result.nii.gz` WMH masks (0/1, no other-pathology label) from two more observers for the 60 training subjects (inter-observer agreement in the paper).
- `readme.pdf`: the challenge website as of December 2022: data description, MRI parameters, evaluation metrics and the final leaderboard.

`tables/` (derived from `source/`):

- `images.tsv`: FLAIR and T1w (desc n/a = `orig/`, `bias` = `pre/`; the 3D T1 resampled to the FLAIR grid is `space-FLAIR` / `space-FLAIR_bias`), and as modality `mask`: `wmh` (the target), `wmh_o3` / `wmh_o4` (training only), and the defacing masks `defaceT1w`, `defaceFLAIR` and `defaceT1w_space-FLAIR` (the last two Amsterdam only).
- `samples.tsv` + `samples.json`: only what the release gives per subject: site (the folder name) and scanner (as named in `readme.pdf`). The template's age and sex columns are left out, since the release has neither.
- `splits.tsv`: split, official split, rank and complete per participant.

## Excluded

- Nothing. The release is images, annotations and `readme.pdf` only.

## Notes

- **Evaluation:** the challenge scores label 1 vs 0 on the FLAIR grid and ignores label-2 voxels, with five metrics: Dice, 95th-percentile Hausdorff distance, average volume difference (%), lesion recall and lesion F1 (code: `evaluation.py` in [hjkuijf/wmhchallenge](https://github.com/hjkuijf/wmhchallenge)). Report on `test` to compare with the published leaderboard.
- **Scanners:** UMC Utrecht 3 T Philips Achieva, NUHS Singapore 3 T Siemens TrioTim, VU Amsterdam 3 T GE Signa HDxt (train + test); VU Amsterdam 3 T Philips Ingenuity and 1.5 T GE Signa HDxt (test only, 10 each), so the test set measures generalization to unseen scanners.
- Label 2 (other pathology) is a rough mask, dilated by one voxel in-plane; where it overlapped WMH, label 1 was kept. It occurs in 67 of the 170 subjects.
- The FLAIR-grid defacing masks (`FLAIR_mask`, `T1_mask`) are interpolated (values in [0, 1]), not binary. `orig/T1_mask.nii.gz` is not mentioned in `readme.pdf`.
- The masks are stored as float32; the label values are exact (0, 1, 2).
