#!/usr/bin/env python3
# 99N_fetch_lipt_age_sex.py - national attendees and treated dyslipidemia by sex and age (KOSIS Open API).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.2, MIT license). See README.md (Pipeline) for how to run.
import os, sys, json, time, urllib.request, urllib.parse
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험")
TBL = sys.argv[1]; Y0, Y1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (2011, 2024)
KEY = os.environ["KOSIS_KEY"]
URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do?"
OUT = os.path.join(SRC, f"{TBL}_national"); os.makedirs(OUT, exist_ok=True); rows = []
for y in range(Y0, Y1 + 1):
    f = os.path.join(OUT, f"{y}.json")
    if not os.path.exists(f):
        q = dict(method="getList", **{'api' + 'Key': KEY}, itmId="ALL", objL1="ALL", objL2="ALL", objL3="ALL", format="json", jsonVD="Y",
                 prdSe="Y", startPrdDe=str(y), endPrdDe=str(y), orgId="350", tblId=TBL)
        d = json.loads(urllib.request.urlopen(URL + urllib.parse.urlencode(q), timeout=300).read().decode("utf-8"))
        if isinstance(d, dict): raise SystemExit(f"[99N-f] {TBL} {y} error response (key removed): {str({k: v for k, v in d.items() if 'key' not in k.lower()})[:300]}")
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False); time.sleep(1)
    d = json.load(open(f, encoding="utf-8"))
    for r in d:
        rows.append(dict(year=int(r["PRD_DE"]), tbl_nm=r.get("TBL_NM"), age_code=r["C1"], age=r["C1_NM"], sex=r["C2_NM"], grp_code=r.get("C3"), grp=r.get("C3_NM"),
                         item=r["ITM_NM"], value=pd.to_numeric(r["DT"], errors="coerce")))
    print(f"[99N-f] {TBL} {y}: {len(d):,} rows")
L = pd.DataFrame(rows); L.to_csv(os.path.join(SRC, f"{TBL}_national_long.csv"), index=False, encoding="utf-8-sig")
print(TBL, L.tbl_nm.iat[0], L.grp.unique().tolist(), L.item.unique().tolist(), L.age.unique().tolist()[:6])
