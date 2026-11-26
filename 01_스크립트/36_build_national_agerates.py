#!/usr/bin/env python3
# 36_build_national_agerates.py - shared helpers for national age-specific rates (10-year age bands, NHIS 298-category Excel reader).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.1, MIT license). See README.md (Pipeline) for how to run.
#  Imported by 38_build_Estd_all.py (and through it by 99L2_build_Estd3_lipt.py); it has no main step of its own.
#  NFC, AGES and age10(): Unicode normalisation and the eight 10-year age bands (0-9 ... 60-69, 70+).
#  excel_year(): reads one yearly NHIS workbook of patients by the 298 disease categories and age (file "<year>_298 ...xlsx").
#    Layout: 2019 has one sheet with the age blocks side by side; 2020-2024 have about 90 sheets with three age blocks each.
#    In both layouts a block starts at a column whose row-5 header is the patient count, and the age label
#    is the text of row 4 over the five block columns.
#  AGEPOP: district population by 10-year age band (columns region, year, age10, pop), read by 38_build_Estd_all.py when it
#    builds the comparison outcomes; set ST_AGEPOP (default data/ST_agepop.csv). The principal pipeline does not read it.
import os, re, unicodedata
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
NFC = lambda s: unicodedata.normalize("NFC", str(s))
AGEPOP = os.environ.get("ST_AGEPOP", os.path.join(ROOT, "data", "ST_agepop.csv"))
AGES = ["0~9세", "10~19세", "20~29세", "30~39세", "40~49세", "50~59세", "60~69세", "70세 이상"]

def age10(lo):   # lower bound of an age group -> 10-year band
    return AGES[min(int(lo) // 10, 7)]

def _code(v):
    s = NFC(v).strip()
    if re.fullmatch(r"\d{1,3}(\.0)?", s): return int(float(s))
    return None

def _agelabel(cells):
    t = re.sub(r"\s+", "", "".join(NFC(c) for c in cells if pd.notna(c)))
    if t.startswith("총") or "G.T" in t or "Total" in t: return "TOTAL"
    n = re.findall(r"\d+", t); assert n, f"age label not parsed: {t}"
    return int(n[0])

def excel_year(f):
    """Return {(code, age lower bound or 'TOTAL'): patients} for one yearly workbook (care type 'total')."""
    X = pd.read_excel(f, sheet_name=None, header=None); vals = {}
    for sn, d in X.items():
        hdr5 = d.iloc[5].map(lambda v: NFC(v).replace("\n", "") if pd.notna(v) else "")
        pcols = [j for j, v in hdr5.items() if v.startswith("진료실인원")]
        assert pcols, f"{f} {sn}: no patient-count column"
        labels = {j: _agelabel(d.iloc[4, j:j + 5].tolist()) for j in pcols}
        for i in range(6, len(d)):
            c = _code(d.iat[i, 0]); kind = NFC(d.iat[i, 1]).replace(" ", "").replace("　", "") if pd.notna(d.iat[i, 1]) else ""
            if c is None or not kind.startswith("계"): continue
            for j in pcols:
                k = (c, labels[j]); v = float(str(d.iat[i, j]).replace(",", "").replace("-", "0"))
                assert k not in vals or vals[k] == v, f"{f}: duplicated cell with different value {k}"
                vals[k] = v
    return vals
