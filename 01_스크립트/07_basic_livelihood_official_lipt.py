# 07_basic_livelihood_official_lipt.py - replace the basic livelihood security rate by the official recipient-based rate (reference SQLite build).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.1, MIT license). See README.md (Pipeline) for how to run.
import os, sys, sqlite3, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", s) if isinstance(s, str) else s
src, dst = sys.argv[1], sys.argv[2]
c = sqlite3.connect(f"file:{os.environ['ST_REF_SQLITE']}?mode=ro", uri=True)
X = pd.read_csv(src, encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
kc = pd.read_sql("select distinct fbd_region, sigungu_cd from region_year", c); kc["fbd_region"] = kc.fbd_region.map(NFC)
assert kc.fbd_region.is_unique and kc.sigungu_cd.is_unique
X = X.merge(kc, on="fbd_region", how="left", validate="many_to_one"); assert X.sigungu_cd.notna().all()
bl = pd.read_sql("select year, sigungu_cd, basic_livelihood_rate_raw as bl from disease_panel where tag='CANM'", c)
for t in [r[0] for r in c.execute("select distinct tag from disease_panel where basic_livelihood_rate_raw is not null")]:
    o = pd.read_sql("select year, sigungu_cd, basic_livelihood_rate_raw as v from disease_panel where tag=?", c, params=(t,)).merge(bl, on=["year", "sigungu_cd"])
    assert np.allclose(o.v, o.bl, equal_nan=True), t
X = X.merge(bl, on=["year", "sigungu_cd"], how="left", validate="one_to_one"); assert X.bl.notna().all()
n = int(((X.basic_livelihood_rate - X.bl).abs() > 1e-9).sum()); X["basic_livelihood_rate"] = X.bl
X.drop(columns=["bl", "sigungu_cd"]).to_csv(dst, index=False, encoding="utf-8-sig"); print("changed cells", n)
