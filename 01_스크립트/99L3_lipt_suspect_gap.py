#!/usr/bin/env python3
# 99L3_lipt_suspect_gap.py - treated versus suspected dyslipidemia.
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.2, MIT license). See README.md (Pipeline) for how to run.
import os, json, unicodedata, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); PAN = os.path.join(ROOT, "02_패널")
NFC = lambda s: unicodedata.normalize("NFC", str(s)); OUT = os.path.join(AN, "LIPT", "results_std3"); os.makedirs(OUT, exist_ok=True)
T = pd.read_csv(os.path.join(PAN, "LIPT_Estd3.csv"), encoding="utf-8-sig"); T["fbd_region"] = T.fbd_region.map(NFC)
Su = pd.concat([pd.read_csv(os.path.join(PAN, f"{t}_Estd3n.csv"), encoding="utf-8-sig") for t in ("LIPSA", "LIPSB")]); Su["fbd_region"] = Su.fbd_region.map(NFC)
assert not Su.duplicated(["year", "fbd_region"]).any()
P = pd.read_csv(os.path.join(AN, "LIPT", "panel_LIPT_std3.csv"), encoding="utf-8-sig"); P["fbd_region"] = P.fbd_region.map(NFC)
cov = P.groupby("fbd_region")[["im_specialists_per_100k_raw", "tertiary_educated_share_raw", "screening_uptake_raw"]].mean()
def agg(y0, y1):
    t = T[T.year.between(y0, y1)].groupby("fbd_region").agg(lipt_cases=("cases", "sum"), lipt_E=("E_std", "sum"), lipt_Epop=("E_pop", "sum"))
    s = Su[Su.year.between(y0, y1)].groupby("fbd_region").agg(susp_cases=("cases", "sum"), susp_E=("E_std", "sum"))
    X = t.join(s, how="inner"); X["SIR_lipt"] = X.lipt_cases / X.lipt_E; X["SIR_lipt_pop"] = X.lipt_cases / X.lipt_Epop; X["SIR_susp"] = X.susp_cases / X.susp_E
    X["G"] = np.log(X.SIR_lipt) - np.log(X.SIR_susp); return X
import geopandas as gpd
SHP = os.environ.get("ST_SHP", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "boundary", "final.shp"))
G = gpd.read_file(SHP); G["region"] = G.region.map(NFC)
L = open(os.path.join(AN, "LIPT", "graph_593.graph")).read().split("\n"); n = int(L[0]); NB = [[] for _ in range(n)]
for ln in L[1:]:
    t = ln.split()
    if len(t) >= 2: NB[int(t[0]) - 1] = [int(x) - 1 for x in t[2:]]
regs = list(G.region); W = np.zeros((n, n))
for i in range(n):
    if NB[i]: W[i, NB[i]] = 1 / len(NB[i])
def moran(y):
    ok = ~np.isnan(y); Wk = W[np.ix_(ok, ok)].copy(); rs = Wk.sum(1); Wk[rs > 0] /= rs[rs > 0, None]; v = y[ok]
    f = lambda u: (len(u) / Wk.sum()) * ((u - u.mean()) @ Wk @ (u - u.mean())) / ((u - u.mean()) @ (u - u.mean()))
    I = f(v); rng = np.random.default_rng(20261111); Ip = np.array([f(rng.permutation(v)) for _ in range(999)]); return I, (np.sum(Ip >= I) + 1) / 1000
S = {}
for nm, (a, b) in {"all_2011-24": (2011, 2024), "W1_2011-17": (2011, 2017), "W2_2018-24": (2018, 2024)}.items():
    X = agg(a, b).join(cov); hiT = X.SIR_lipt > 1; hiS = X.SIR_susp > 1
    X["quadrant"] = np.select([hiT & ~hiS, ~hiT & hiS, hiT & hiS], ["treated high / suspected low", "treated low / suspected high", "both high"], "both low")
    X["sido"] = X.index.str[:2]; I, p = moran(X.reindex(regs).G.values)
    r = lambda u, v: round(spearmanr(X[u], X[v]).correlation, 3)
    S[nm] = dict(n=int(len(X)), rho_lipt_susp=r("SIR_lipt", "SIR_susp"), rho_liptpop_susp=r("SIR_lipt_pop", "SIR_susp"), quadrants=X.quadrant.value_counts().to_dict(),
                 moran_G=round(I, 3), moran_G_p=round(p, 4), rho_G_im=r("G", "im_specialists_per_100k_raw"), rho_G_tertiary=r("G", "tertiary_educated_share_raw"), rho_G_uptake=r("G", "screening_uptake_raw"),
                 rho_lipt_im=r("SIR_lipt", "im_specialists_per_100k_raw"), rho_susp_im=r("SIR_susp", "im_specialists_per_100k_raw"),
                 rho_lipt_tertiary=r("SIR_lipt", "tertiary_educated_share_raw"), rho_susp_tertiary=r("SIR_susp", "tertiary_educated_share_raw"),
                 quadrant_by_sido=pd.crosstab(X.sido, X.quadrant).to_dict())
    if nm == "all_2011-24": X.round(4).to_csv(os.path.join(OUT, "S50_lipt_suspect_gap.csv"), encoding="utf-8-sig"); print(pd.crosstab(X.sido, X.quadrant))
json.dump(S, open(os.path.join(OUT, "S50_lipt_suspect_gap_summary.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "quadrant_by_sido"} for k, v in S.items()}, ensure_ascii=False, indent=1))
