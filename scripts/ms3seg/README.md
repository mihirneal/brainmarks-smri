# MS3SEG: multiple sclerosis lesions

Clinical MRI of 100 patients with multiple sclerosis from one imaging center in Tabriz, Iran (Golgasht Medical Imaging Center), on one 1.5 T Toshiba Vantage Elan. We use it for MS lesion segmentation on FLAIR.

- **Homepage:** <https://github.com/Mahdi-Bashiri/MS3SEG>
- **Source:** figshare [10.6084/m9.figshare.30393475](https://doi.org/10.6084/m9.figshare.30393475), downloaded with `curl` (one URL per file ID) and checked against figshare's md5. The release is in RAR archives: we extract them with 7-Zip (`7zz`), keeping only the files listed under Contents.
- **Version:** figshare version 6 (2026-06-21), the latest as of 2026-11-19.
- **DOI:** [10.6084/m9.figshare.30393475.v6](https://doi.org/10.6084/m9.figshare.30393475.v6)
- **License:** CC BY 4.0
- **Citation:** Bashiri Bawil, M., Shamsi, M., Ghalehasadi, A., Jafargholkhanloo, A. F., & Shakeri Bavil, A. (2026). A multiple sclerosis MRI dataset with tri-mask annotations for lesion segmentation. *Scientific Data*. [doi:10.6084/m9.figshare.30393475](https://doi.org/10.6084/m9.figshare.30393475)
- **Code:** [`scripts/ms3seg/`](https://github.com/MedARC-AI/brainmarks-smri/tree/main/scripts/ms3seg) downloads `source/` and builds `tables/`, `derivatives/` and `shards/`.

## Samples

One sample per patient (100), each with a FLAIR and an MS lesion mask. Every patient has lesions. Dev/test is 50/50 by participant, stratified by lesion volume tertile; there is no official split.

| split | participants | age | female | ms_lesion_volume | ms_lesion_count |
|---|---|---|---|---|---|
| dev | 51 | 37.1 ± 9.6 | 73% | 11.9 ± 10.9 | 29.8 ± 13.6 |
| test | 49 | 33.8 ± 7.7 | 76% | 13.6 ± 12.6 | 35.9 ± 21.2 |
| total | 100 | 35.5 ± 8.8 | 74% | 12.7 ± 11.7 | 32.8 ± 17.9 |

## Contents

`source/`: part of the release (300 files, 196 MB):

- `MS_100_patient_nifti/<patient>/<patient>_FLAIR.nii.gz` + `.json`: the 2D axial FLAIR (256 × 256 × ~20, 0.9 × 0.9 mm in plane, 6 mm slices 6.8 mm apart) and its sidecar, with age and sex.
- `MS_100_patient_masks/abWMH_Masks/<patient>/<patient>_abWMH_Mask.nii.gz`: the expert MS lesion (abnormal white matter hyperintensity) mask, on the FLAIR grid, 0/255.

`tables/` (derived from `source/`):

- `images.tsv`: FLAIR and the lesion mask (modality `mask`, desc `lesion`).
- `samples.tsv` + `samples.json`: age and sex (from the FLAIR sidecars), and the lesion volume (ml) and count (26-connected components) of the mask. `site` is n/a (one center).
- `splits.tsv`: dev or test per participant.

## Excluded

- The T1w and T2w images (`_T1WI`, `_T2WI`) and the sagittal FLAIR (`_FLAIR_SG`): no task uses them.
- The ventricle masks (`Vent_Masks`) and the normal periventricular hyperintensity masks (`nWMH_Masks`): no task uses them.
- The other archives of the release (`MS_100_patient_full`, `_preprocessed`, `_registered`, `_model_input`, `_gifs`): DICOM, the authors' preprocessed and registered copies, model inputs and previews.

## Notes

- The masks are stored as floats with values 0 and ~255 (254.99999994); the task counts any nonzero voxel as lesion.
- With ~7 mm between slices, the FLAIR covers about 136 mm head to foot.
