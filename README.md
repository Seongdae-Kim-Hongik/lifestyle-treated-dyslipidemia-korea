# Do lifestyle risk factors explain where Koreans report treated dyslipidemia?

Analysis code for the manuscript

> *Do lifestyle risk factors explain where Koreans report treated dyslipidemia?*

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24560215 (v1.0.2). Released under the MIT license.

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected counts and result tables) and the boundary file are not included; they are available from the author on reasonable request. Every intermediate file is rebuilt by the scripts below from the public inputs listed under Environment variables (the master table from the reference dataset, the adjacency graph from the boundary file). All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/LIPT/sets_LIPT_*.json`, `config_LIPT_std3.json` | Covariates, expected directions, forced controls and model settings (principal model `std3`; sensitivity versions `s577`, `s2`, `s8`) |
| `04_분석/LIPT/MS/` | Scripts that read the result tables and write every number, table and figure in the manuscript and Supplementary Material, including `content_lipt.py` and `content_manuscript_lipt.py`, which generate the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder names, file names, column names and region names are in Korean because the source tables are Korean (see Korean identifiers below); code comments and printed messages are in English. Every script in `01_스크립트/` and `04_분석/LIPT/` starts with a short English header naming its purpose. Inputs and outputs are listed in the Pipeline table below; the outputs (panels, result tables, figures and reports) are written locally when the code is run and are not part of this repository.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- General health screening attendees (DT_35007_N098, N099) and judgment results by disease, district (N105) and by sex and age group (N106): National Health Insurance Service via KOSIS, 2011-2024. Outcome: attendees in the existing-disease category for dyslipidemia (already diagnosed and on drug treatment); comparison: the suspected-disease category.
- Population by sex and age group: Ministry of the Interior and Safety, resident registration statistics (Changwon 2023 corrected; `population_override`).
- District covariates: KOSIS, the Community Health Survey, National Health Insurance Service screening statistics, Health Insurance Review and Assessment Service specialist counts, the census (tertiary education) and public sports facility surveys. Comparison outcomes (people treated for gastric cancer and for infectious diseases) come from National Health Insurance regional statistics.
- Reference district-year dataset (SQLite; set `ST_REF_SQLITE`): district-year skeleton, master table (`source_master_all_years`), official basic livelihood security rate, and checks of outcome and denominator values. Its covariate folder (`01_공변량_229x2011_2024.csv`, `00_시군구_229_대응표.csv`) is read through `ST_CANON`.

## Unpacking

On macOS, unpack the archive with `ditto -x -k <zip> <folder>` or Python (`python3 -c "import zipfile, sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" <zip> <folder>`); the system `unzip` may fail on the Korean folder names.

## Environment variables

| Variable | Read by | What to set |
|---|---|---|
| `ST_REF_SQLITE` | `45`, `99L2`, `07` | Path of the reference district-year dataset (SQLite file, opened read-only) |
| `ST_FBDZIP` | `99L2` (through `38_build_Estd_all.py`) | Folder of resident population by sex and 5-year age group, one file per year (`<year>.csv`, 2011-2024), with the corrected Changwon 2023 values. `run_std3_chain.sh` also accepts the older name `ST_FBDZIP_CORRECTED` |
| `ST_CANON` | `99c` | Covariate folder of the reference dataset holding `01_공변량_229x2011_2024.csv` and `00_시군구_229_대응표.csv`; if unset, `$ST_DATA_ROOT/기타/R_Studio/FBD_DATA_ZIP/통합자료_261030` is used |
| `ST_SHP` | `41`, `80`, `81`, `85`, `86`, `88*`, `99L3`, `plus1_check_lipt.R` | District boundary shapefile (229 districts, 2024 boundaries); default `data/boundary/final.shp` |
| `ST_GRAPH` | `81`, `85`, `88k`, `88L*`, `plus1_check_lipt.R` | Principal adjacency graph, `04_분석/LIPT/graph_593.graph` written by `41_build_graph.py` (229 districts, 593 links); set by `run_std3_chain.sh` |
| `KOSIS_KEY` | `99N`, `32L` | Own KOSIS Open API key; needed only when a source table is not yet on disk |
| `ST_VER`, `TAG` | `80` (through `_st_config.py`), `81`, `88*` | Model version (`std3`, or `s577`, `s2`, `s8`) and outcome tag (`LIPT`); set by `run_std3_chain.sh` |
| `ST_THREADS` | `81` | INLA threads per model (the chain uses 1) |
| `ST_MV_STOP`, `ST_MV_RANGE`, `ST_MV_N` | `81` | `ST_MV_STOP=1` stops after writing the multiverse specification; `ST_MV_RANGE=a-b` fits multiverse subsets a to b (part files merged by the next main run); `ST_MV_N` overrides the multiverse size (2 for the sensitivity versions) |
| `GROUP`, `NCO`, `FOCAL`, `SMOOTH`, `DROPS`, `NS`, `SUB`, `KH_INIT`, `ROBV_OVERRIDE` | `88g`, `88h`, `88k` | Sensitivity group (1-6), comparison outcomes (`INFECT,GCA`) and optional settings of the sensitivity and Knorr-Held scripts; the chain sets `GROUP` and `NCO` |
| `SK_RSLOTS` | `rslot.sh` | Maximum number of concurrent R jobs (default 9) |
| `ST_DATA_ROOT` | `38`, `40`, `50` (defaults only) | Not needed for steps 1-5 when `ST_FBDZIP` and `ST_CANON` are set |
| `ST_AGEPOP` | `38_build_Estd_all.py` (comparison outcomes only) | District population by 10-year age band; default `data/ST_agepop.csv` |
| `ST_DATA_GATE` | `run_std3_chain.sh` | Optional path of a pre-model data-check script (not part of this repository) |

## Pipeline

Run from the repository root after setting the environment variables above; `bash 04_분석/LIPT/run_std3_chain.sh` runs steps 1 to 7 in order. R jobs are run through `01_스크립트/rslot.sh`, which limits the number of concurrent single-threaded INLA fits. Folders `00_원천/` (KOSIS source tables) and `02_패널/` (intermediate tables) are created by the scripts.

| Step | Script | Output |
|---|---|---|
| 1 | `99N_fetch_lipt_age_sex.py DT_35007_N099`, `99N_fetch_lipt_age_sex.py DT_35007_N106` (KOSIS Open API, `KOSIS_KEY`) | National attendees (N099) and treated dyslipidemia (N106) by sex and age group: `00_원천/C_NHIS_검진보험/DT_35007_N099_national_long.csv`, `DT_35007_N106_national_long.csv` |
| 1b | `32L_checkup_district_long.py`; `45_master_from_refdataset.py`; `41_build_graph.py` | District attendees (N098) and existing-disease judgments (N105) by sex, from `00_원천/C_NHIS_검진보험/DT_35007_N098.csv` and `DT_35007_N105.csv` (downloaded from KOSIS when missing) into `02_패널/NHIS검진_시군구_연도_long.csv`; master table `02_패널/MASTER_시군구_연도_wide.parquet` read from table `source_master_all_years` of `ST_REF_SQLITE` (the same table that `50_build_master_panel.py` builds from source-specific wide files, which are not distributed); adjacency graph `04_분석/LIPT/graph_593.graph` from `ST_SHP` (queen contiguity, islands linked to the nearest centroid) |
| 2 | `99L2_build_Estd3_lipt.py` (imports `38_build_Estd_all.py` with `36_build_national_agerates.py`, `40_region_crosswalk.py`, `50_build_master_panel.py`) | Inputs: step 1 and 1b tables, `ST_FBDZIP`, and the district-year skeleton (`region_year`) and outcome check of `ST_REF_SQLITE`. Output `02_패널/LIPT_Estd3.csv`: district counts, expected numbers standardized by sex and age among attendees, resident-based expected numbers, share of residents aged 80+ |
| 3 | `99c_extra_canonical_pool_lipt.py`, then `07_basic_livelihood_official_lipt.py 02_패널/EXT_canonical_pool_LIPT_261111.csv 02_패널/EXT_canonical_pool_LIPT_261111.csv` (source and destination; the file is rewritten in place) | Specialists, tertiary education, basic livelihood security and unmet need joined by district code (`ST_CANON`, master table), plus `02_패널/EXT_undx_dxshare_261110.csv` (shares already diagnosed with hypertension or diabetes, sensitivity only); the basic livelihood security rate is then replaced by the official recipient-based rate of `ST_REF_SQLITE`. Run 07 after every 99c run |
| 4 | `80_build_disease_panel_v.py LIPT` (`ST_VER=std3`; reads the master table, `LIPT_Estd3.csv`, both step 3 files and `ST_SHP`) | Analytic panel `04_분석/LIPT/panel_LIPT_std3.csv` |
| 5 | `81_fit_inla.R LIPT` (`ST_VER=std3`, `ST_GRAPH=04_분석/LIPT/graph_593.graph`, `ST_THREADS=1`; see `04_분석/LIPT/run_std3_chain.sh`) | Principal model, set comparison, 200-subset multiverse, window models |
| 6 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `87_window_grid.py` | Window maps and emerging hot spot analysis |
| 7 | `88g_sens_prep.py LIPT std3 INFECT,GCA`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh.R` (nb, struct, review), `88k_struct_kh_lipt.R` with `kh_constraints_lipt.R` (kh), `89g_sens_combine.py` | Sensitivity analyses, comparison outcomes, Knorr-Held models, review outputs |
| 8 | `88L_lipt_reverse_posthoc.R`, `88L_P5fix_lipt.R`, `88L2_lipt_mpa_precise.R`, `plus1_check_lipt.R` | Post hoc examination of specialist density (specialists per area = specialist count divided by area); unrounded interval for physical activity; check that no constant is added to the offset and that the log(1 + x) transform does not drive the results |
| 9 | `99L3_lipt_suspect_gap.py` | Treated versus suspected dyslipidemia |
| 10 | `04_분석/LIPT/MS/build/run_all_lipt.sh` (`build_refs_lipt.py`, `figs_lipt.py`, `build_manuscript_lipt.py`, `build_supplement_lipt.py`, engine `docx_engine.py`) | Manuscript, title page, Supplementary Material and figures |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path. `85_window_maps.R`, `86_yearly_maps_ehsa.py` and `87_window_grid.py` take the version as their second argument (default `std3`, the principal model).

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx. Newer INLA may shift DIC/WAIC a few points without changing any IRR. Each INLA fit uses one thread (`num.threads = "1:1"`).

## Changes in v1.0.2

- Removed a list of identifiers used only by a private manuscript check and a hard-coded contact address from the manuscript builder; contact details are now supplied at build time (`LIPT_EMAIL`, `LIPT_PHONE`).
- Comments, docstrings and printed messages are in English; Korean remains only in data identifiers (see Korean identifiers).
- Tool paths are found on the system path (`SOFFICE`, `PDFTOTEXT`) and temporary folders use the system default; paragraph properties in the generated Word files follow the schema order.
- The internal summary-report scripts were removed (they produce no manuscript output). No numerical change.

## Changes in v1.0.1

Public code tidy-up; no change to any number, table or figure.

- `88L_P5fix_lipt.R` restored (the file was empty in v1.0.0).
- Code comments checked so that all are in English; script headers updated to v1.0.1.
- The boundary file in `99L3_lipt_suspect_gap.py` is read from `ST_SHP`, as in the other scripts.
- The default version argument of `85_window_maps.R`, `86_yearly_maps_ehsa.py` and `87_window_grid.py` is `std3`, matching the commands above.
- The internal summary-report scripts used during analysis are not part of this repository (they do not produce any manuscript output); in `04_분석/LIPT/run_std3_chain.sh` the optional pre-model data check runs only when `ST_DATA_GATE` is set.
- Scripts that were needed but missing are added: `36_build_national_agerates.py` (helpers imported by `38_build_Estd_all.py`; the hard-coded population path is replaced by `ST_AGEPOP`), `32L_checkup_district_long.py` (district screening tables N098 and N105 from KOSIS), `45_master_from_refdataset.py` (master table from the reference dataset) and `41_build_graph.py` (adjacency graph from the boundary file; the result is identical to the graph used for the published models).
- `99L2_build_Estd3_lipt.py` takes the district-year skeleton from the reference dataset and computes the share of residents aged 80+ from `ST_FBDZIP`, instead of reading panels of other outcomes; `99c_extra_canonical_pool_lipt.py` also writes `EXT_undx_dxshare_261110.csv`. The expected-count file, covariate pool and analytic panel built this way are byte-identical to those behind the manuscript.
- `run_std3_chain.sh` runs steps 1, 1b and `07_basic_livelihood_official_lipt.py` (with its source and destination arguments) before the panel step, so that the panel uses the official basic livelihood security rate; it reads `ST_FBDZIP` (the older name `ST_FBDZIP_CORRECTED` is still accepted).
- README: environment variable table (names as read by the code, including `ST_CANON`), unpacking note, and the inputs of each pipeline step.

## Korean identifiers

The source statistics and the reference dataset are published in Korean, and the code reads their file names, folder names, column names, category values and region names exactly as they appear there, so these Korean strings have not been translated: translating them would stop the code from finding its inputs or matching their values. The same applies to the Korean names of intermediate files that one script writes and another reads, to the Korean labels that the core report uses and its check script looks for, and to the Korean values written to the master table and its variable dictionary. Apart from the Korean core result report described under Contents, every other piece of text in the code (comments, messages, assertion texts and the merge and key check reports) is in English.
