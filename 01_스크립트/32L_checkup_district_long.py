#!/usr/bin/env python3
# 32L_checkup_district_long.py - district screening attendees (N098) and existing-disease judgments (N105) by sex, long format.
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.1, MIT license). See README.md (Pipeline) for how to run.
#  Input:  KOSIS tables DT_35007_N098 and DT_35007_N105 (orgId 350), 2011-2024, saved as <table>.csv in the NHIS source folder
#          (see README, Pipeline step 1b). A missing table is downloaded year by year through the KOSIS Open API
#          (own key in KOSIS_KEY); a table already on disk is used as it is.
#  Output: the district-year long table of screening statistics (NHIS*_long.csv) in the panel folder, read by 99L2_build_Estd3_lipt.py
#          (columns year, sido, sigungu, level, sex, topic, category, measure, unit, value, tbl_id).
#  Region rule: C1 code of 12 characters = province (ending Z1 = national total); 14 or more characters = district, whose
#  first 12 characters give the province. Category labels follow the KOSIS code hierarchy (parent_child).
import os, sys, json, time, urllib.request, urllib.parse
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험"); OUT = os.path.join(ROOT, "02_패널")
os.makedirs(SRC, exist_ok=True); os.makedirs(OUT, exist_ok=True)
Y0, Y1 = 2011, 2024
SIDO_SHORT = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주",
    "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원도": "강원",
    "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남", "전라북도": "전북", "전북특별자치도": "전북",
    "전라남도": "전남", "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주", "제주도": "제주",
    "계": "전국", "전체": "전국", "합계": "전국",
}
SGG_ALIAS = {("부산", "진구"): "부산진구"}      # district name alias across tables
SGG_SIDO_FIX = {"여주시": "경기"}              # district whose province prefix is wrong in some KOSIS codes
TBL = {"DT_35007_N098": dict(topic="일반검진_판정", override={"004": "질환의심", "00401": "계"}),
       "DT_35007_N105": dict(topic="일반검진_유질환자세부", override={"003": ""})}
URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do?"

def fetch(tbl):
    """Download one table year by year (JSON cache in <table>_sgg/) and write <table>.csv."""
    key = os.environ.get("KOSIS_KEY"); assert key, f"{tbl}.csv not found and KOSIS_KEY not set"
    cache = os.path.join(SRC, f"{tbl}_sgg"); os.makedirs(cache, exist_ok=True); parts = []
    for y in range(Y0, Y1 + 1):
        f = os.path.join(cache, f"{y}.json")
        if not os.path.exists(f):
            q = dict(method="getList", **{"api" + "Key": key}, itmId="ALL", objL1="ALL", objL2="ALL", objL3="ALL", format="json", jsonVD="Y",
                     prdSe="Y", startPrdDe=str(y), endPrdDe=str(y), orgId="350", tblId=tbl)
            d = json.loads(urllib.request.urlopen(URL + urllib.parse.urlencode(q), timeout=300).read().decode("utf-8"))
            if isinstance(d, dict): raise SystemExit(f"[32L] {tbl} {y}: error response {str({k: v for k, v in d.items() if 'key' not in k.lower()})[:300]}")
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False); time.sleep(1)
        parts.append(pd.DataFrame(json.load(open(f, encoding="utf-8"))))
        print(f"[32L] {tbl} {y}: {len(parts[-1]):,} rows")
    pd.concat(parts, ignore_index=True).to_csv(os.path.join(SRC, f"{tbl}.csv"), index=False, encoding="utf-8-sig")

def build_labels(codes_nm, override):
    labels = dict(codes_nm); labels.update(override or {}); keys = set(labels); out = {}
    def lab(c):
        if c in out: return out[c]
        parent = None
        for k in range(len(c) - 1, 2, -1):
            if c[:k] in keys: parent = c[:k]; break
        own = labels[c]
        if own.startswith("="): res = own[1:]
        elif parent is None: res = own
        else:
            p = lab(parent); res = own if p == "" else (p if own == "" else f"{p}_{own}")
        out[c] = res; return res
    for c in keys: lab(c)
    return out

def parse_region(d):
    code = d["C1"].astype(str); name = d["C1_NM"].astype(str).str.strip(); L = code.str.len()
    is_nat = code.str.endswith("Z1") & (L == 12); is_sido = (L == 12) & ~is_nat
    sido_map = dict(zip(code[is_sido], name[is_sido].map(lambda s: SIDO_SHORT.get(s, s))))
    level = np.where(is_nat, "전국", np.where(is_sido, "시도", "시군구"))
    sido = pd.Series(np.where(is_nat, "전국", code.str[:12].map(sido_map)), index=d.index)
    sgg = pd.Series(np.where(level == "시군구", name.str.replace(r"\s+", "", regex=True), "계"), index=d.index)
    sgg = pd.Series([SGG_ALIAS.get((s, g), g) for s, g in zip(sido, sgg)], index=d.index)
    fix = (level == "시군구") & sgg.isin(SGG_SIDO_FIX); sido = sido.where(~fix, sgg.map(SGG_SIDO_FIX))
    return sido, sgg, pd.Series(level, index=d.index)

def load_table(tbl):
    p = os.path.join(SRC, f"{tbl}.csv")
    if not os.path.exists(p): fetch(tbl)
    cfg = TBL[tbl]; d = pd.read_csv(p, dtype=str, encoding="utf-8-sig", low_memory=False)
    d = d.replace({"DT": {"-": np.nan}}); d["value"] = pd.to_numeric(d.DT.str.replace(",", "", regex=False), errors="coerce")
    d["sido"], d["sigungu"], d["level"] = parse_region(d)
    d["year"] = d.PRD_DE.astype(int); d["sex"] = d["C2_NM"].str.strip().replace({"계": "합계"})
    lab = build_labels(dict(zip(d["C3"], d["C3_NM"].str.strip())), cfg["override"])
    d["category"] = d["C3"].map(lab).str.replace(r"\s+", " ", regex=True)
    d["topic"] = cfg["topic"]; d["measure"] = d.ITM_NM.str.strip(); d["unit"] = d.UNIT_NM.str.strip(); d["tbl_id"] = tbl
    d = d[d.year.between(Y0, Y1)]
    return d[["year", "sido", "sigungu", "level", "sex", "topic", "category", "measure", "unit", "value", "tbl_id"]]

long = pd.concat([load_table(t) for t in TBL], ignore_index=True)
key = ["year", "sido", "sigungu", "sex", "topic", "category", "measure"]
print(f"[32L] duplicated keys dropped (first kept): {int(long.duplicated(key).sum())}")
long = long[~long.duplicated(key, keep="first")].sort_values(["topic", "year", "sido", "sigungu", "sex", "category", "measure"]).reset_index(drop=True)
fp = os.path.join(OUT, "NHIS검진_시군구_연도_long.csv"); long.to_csv(fp, index=False, encoding="utf-8-sig")
sg = long[long.level == "시군구"]
print(f"[32L] {fp}: {len(long):,} rows, district rows {len(sg):,}, districts per year {sg[['year', 'sido', 'sigungu']].drop_duplicates().groupby('year').size().to_dict()}")
