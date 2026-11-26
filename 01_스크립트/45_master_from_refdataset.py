#!/usr/bin/env python3
# 45_master_from_refdataset.py - district-year master table read from the reference district-year dataset.
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.2, MIT license). See README.md (Pipeline) for how to run.
#  Writes the master table MASTER_*_wide.parquet in the panel folder (read by 99L2, 99c and 80) from table source_master_all_years of the
#  reference SQLite file (ST_REF_SQLITE, opened read-only). This replaces the upstream wide-file build (50_build_master_panel.py),
#  whose source-specific inputs are not distributed; both give the same table (same columns, order and values).
import os, sqlite3, unicodedata
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ["ST_REF_SQLITE"]
PAN = os.path.join(ROOT, "02_패널"); os.makedirs(PAN, exist_ok=True)
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
M = pd.read_sql_query("SELECT * FROM source_master_all_years", con); con.close()
M.columns = [unicodedata.normalize("NFC", c) for c in M.columns]
assert {"year", "key", "fbd_region", "population", "chk__유질환자_이상지질혈증"} <= set(M.columns), "master columns missing"
assert M.groupby("year").key.nunique().nunique() == 1, "district count differs by year"
M.to_parquet(os.path.join(PAN, "MASTER_시군구_연도_wide.parquet"), index=False)
print(f"[45] MASTER {M.shape[0]} rows x {M.shape[1]} columns, years {M.year.min()}-{M.year.max()} -> {PAN}")
