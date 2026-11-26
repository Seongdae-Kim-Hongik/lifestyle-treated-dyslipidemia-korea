#!/usr/bin/env python3
# 99L2_build_Estd3_lipt.py - district counts and sex-by-age standardized expected numbers.
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.2, MIT license). See README.md (Pipeline) for how to run.
import os, io, sys, json, importlib.util, unicodedata, sqlite3
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); PAN = os.path.join(ROOT, "02_패널")
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험"); os.makedirs(PAN, exist_ok=True)
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m38 = _load("m38", "38_build_Estd_all.py"); cw = _load("cw", "40_region_crosswalk.py"); m50 = _load("m50", "50_build_master_panel.py")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
TAG = "LIPT"; YEARS = list(range(2011, 2025))
BANDS = ["0-19"] + [f"{lo}-{lo+4}" for lo in range(20, 85, 5)] + ["85+"]
SEXES = ["남자", "여자"]; OUTS = {"": "00304"}
assert os.environ.get("ST_FBDZIP"), "set ST_FBDZIP (folder with the corrected 2023 Changwon population)"
def nb_band(a):
    a = str(a).replace(" ", "")
    if a == "19세이하": return "0-19"
    if a == "85세이상": return "85+"
    if a.endswith("세") and "~" in a:
        lo, hi = a[:-1].split("~"); return f"{lo}-{hi}"
    return None
A = pd.read_csv(os.path.join(SRC, "DT_35007_N099_national_long.csv"), encoding="utf-8-sig"); A = A[(A.grp == "계") & A.year.isin(YEARS)]
B = pd.read_csv(os.path.join(SRC, "DT_35007_N106_national_long.csv"), encoding="utf-8-sig", dtype={"grp_code": str}); B = B[B.grp_code.isin(OUTS.values()) & B.year.isin(YEARS)]
for X in (A, B): X["band"] = X.age.map(nb_band)
AT = A[A.age == "계"].set_index(["year", "sex"]).value
EX = A[A.band.notna() & A.sex.isin(SEXES)].set_index(["year", "sex", "band"]).value.unstack()[BANDS]
for s in SEXES: assert (abs(EX.xs(s, level="sex").sum(1) - AT.xs(s, level="sex")) <= 1).all(), s
RATE, NUM = {}, {}
for suf, code in OUTS.items():
    b = B[B.grp_code == code]; bt = b[b.age == "계"].set_index(["year", "sex"]).value
    NUM[suf] = b[b.band.notna() & b.sex.isin(SEXES)].set_index(["year", "sex", "band"]).value.unstack()[BANDS].fillna(0)
    for s in SEXES: assert (abs(NUM[suf].xs(s, level="sex").sum(1) - bt.xs(s, level="sex")) <= 1).all(), (suf, s)
    RATE[suf] = NUM[suf] / EX
print("[99L2] national share with existing disease (%, both sexes) by year:", (100 * NUM[""].groupby(level="year").sum().sum(1) / EX.groupby(level="year").sum().sum(1)).round(2).to_dict())
# District-year skeleton (229 districts x 2011-2024, ordered by key and year) from the reference dataset (ST_REF_SQLITE, read-only).
DB = os.environ["ST_REF_SQLITE"]; con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
base = pd.read_sql("select year, key, fbd_region from region_year where year between 2011 and 2024", con); base["fbd_region"] = base.fbd_region.map(NFC); base["key"] = base.key.map(NFC)
base = base.drop_duplicates().sort_values(["key", "year"]).reset_index(drop=True); assert len(base) == 229 * len(YEARS) and base.key.nunique() == 229
PKEYS = set(base.key); SIDO_HDR = {k for k in cw.SIDO_STD if len(k) >= 3 and (k.endswith("시") or k.endswith("도"))}
FIVE = [f"{lo}-{lo+4}세" for lo in range(0, 85, 5)]; OLD85 = ["85-89세", "90-94세", "95-99세", "100세 이상"]
EXTRA = {("충청북도", "청원군"): "충청북도|청주시"}; rows = []; rows80 = []
for y in YEARS:
    d = pd.read_csv(os.path.join(m38.FBDZIP, f"{y}.csv"), encoding="cp949", dtype=str)
    d["행정구역별"] = d["행정구역별"].map(NFC).str.strip(); d["연령별"] = d["연령별"].map(NFC).str.strip()
    for s in ["전체"] + SEXES: d[s] = pd.to_numeric(d[s].str.replace(",", ""), errors="coerce")
    sido = None; city = None; blocks = (d["행정구역별"] != d["행정구역별"].shift()).cumsum()
    for _, g in d.groupby(blocks, sort=False):
        nm = g["행정구역별"].iat[0]
        if nm == "전국": continue
        if nm in SIDO_HDR:
            sido = nm; city = None
            if nm != "세종특별자치시": continue
            g = g.drop_duplicates("연령별")
        sg = nm.split("-")[-1]
        if sg.endswith("시"): city = sg
        elif sg.endswith("구") and city is not None and cw.sido_std(sido) not in ("서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시"): continue
        else: city = None
        key = EXTRA.get((cw.sido_std(sido), sg), cw.make_key(sido, sg))
        if key not in PKEYS and key.endswith("군") and key[:-1] + "시" in PKEYS: key = key[:-1] + "시"
        # Share of residents aged 80+ (%, both sexes): (80-84 + 85+) / total, with 85+ = total - sum of the 5-year groups below 85.
        a = pd.to_numeric(g.set_index("연령별")["전체"], errors="coerce"); t_ = a.get("계", np.nan)
        if pd.notna(t_):
            f_ = a.reindex(FIVE); assert f_.notna().all(), (y, nm)
            rows80.append({"year": y, "key": NFC(key), "tot": t_, "p80": f_["80-84세"] + (t_ - f_.sum())})
        for s in SEXES:
            a = g.set_index("연령별")[s]; tot = a.get("계", np.nan)
            if pd.isna(tot): continue
            f = a.reindex(FIVE); o = a.reindex(OLD85).fillna(0); assert f.notna().all(), (y, nm, s)
            assert abs(tot - f.sum() - o.sum()) < 0.5, (y, nm, s)
            rows.append({"year": y, "sex": s, "key": NFC(key), "tot": tot, "0-19": f["15-19세"], **{b: f[b + "세"] for b in BANDS[1:-1]}, "85+": o.sum()})
G = pd.DataFrame(rows).groupby(["year", "key", "sex"], as_index=False)[["tot"] + BANDS].sum()
NATPOP = G.groupby(["year", "sex"])[BANDS].sum(); UPT = EX / NATPOP
L = pd.read_csv(os.path.join(PAN, "NHIS검진_시군구_연도_long.csv"), usecols=["year", "sido", "sigungu", "level", "sex", "category", "value", "tbl_id"], engine="pyarrow")
CAT = {"계": "exam", "이상지질혈증": "c"}
L = L[L.tbl_id.isin(["DT_35007_N098", "DT_35007_N105"]) & (L.level == "시군구") & L.year.isin(YEARS) & L.sex.isin(SEXES) & L.category.isin(CAT.keys())].copy()
L = L[~((L.tbl_id == "DT_35007_N105") & (L.category == "계"))]; assert not ((L.tbl_id == "DT_35007_N098") & (L.category == "이상지질혈증")).any(); L["v"] = L.category.map(CAT)
pairs = L[["sido", "sigungu"]].drop_duplicates(); mp = {(a, b): m50.map_region(a, b, PKEYS) for a, b in zip(pairs.sido, pairs.sigungu)}
L["key"] = [mp[(a, b)]["key"] for a, b in zip(L.sido, L.sigungu)]; L["role"] = [mp[(a, b)]["role"] for a, b in zip(L.sido, L.sigungu)]
L = L[L.key.notna()]; L["key"] = L.key.map(NFC)
hasprim = L[L.role == "primary"].groupby(["key", "year"]).size().index
L = L[~((L.role == "sub") & L.set_index(["key", "year"]).index.isin(hasprim))]
SX = L.pivot_table(index=["year", "key"], columns=["v", "sex"], values="value", aggfunc="sum")
P = base[base.year.isin(YEARS)].merge(SX.reset_index().droplevel(1, axis=1).iloc[:, :2], on=["year", "key"], how="inner") if False else None
k = base[base.year.isin(YEARS)].set_index(["year", "key"]).index
S = SX.reindex(k); ok = S.notna().all(axis=1) & (S[("exam", "남자")] > 0) & (S[("exam", "여자")] > 0)
ok = ok & ~base[base.year.isin(YEARS)].reset_index(drop=True).fbd_region.eq(NFC("세종시세종시")).values
P = base[base.year.isin(YEARS)].reset_index(drop=True)[ok.values].reset_index(drop=True); S = S[ok.values]
assert P.groupby("fbd_region").year.nunique().eq(len(YEARS)).all() and P.fbd_region.nunique() == 228
print(f"[99L2] district-years {len(k)}, observed {len(P)}; excluded {sorted(set(map(tuple, base[base.year.isin(YEARS)].reset_index(drop=True)[~ok.values][['year','fbd_region']].values.tolist())))[:12]}")
P["examinees"] = (S[("exam", "남자")] + S[("exam", "여자")]).values
for suf in OUTS: P["cases" + suf] = (S[("c" + suf, "남자")] + S[("c" + suf, "여자")]).values
MA = pd.read_parquet(os.path.join(PAN, "MASTER_시군구_연도_wide.parquet"), columns=["year", "fbd_region", "chk__유질환자_이상지질혈증"])
MA["fbd_region"] = MA.fbd_region.map(NFC)
c = P.merge(MA, on=["year", "fbd_region"], how="left", validate="one_to_one")
dd = (c["cases"] - c["chk__유질환자_이상지질혈증"]).abs(); print(f"[99L2] MASTER check: {int(dd.notna().sum())} overlapping cells, max difference {dd.max():.0f}, missing in MASTER (filled from source-table sums) {int(c['chk__유질환자_이상지질혈증'].isna().sum())} cells {c.loc[c['chk__유질환자_이상지질혈증'].isna(), ['fbd_region','year']].values.tolist()}"); assert dd.max() <= 2
SQ = pd.read_sql('select year, fbd_region, "chk__유질환자_이상지질혈증" as sq from region_year where year between 2011 and 2024', con); SQ["fbd_region"] = SQ.fbd_region.map(NFC)
c = P.merge(SQ, on=["year", "fbd_region"], how="left", validate="one_to_one"); dd = (c.cases - c.sq).abs()
print(f"[99L2] reference SQLite check: {int(dd.notna().sum())} overlapping cells, max difference {dd.max():.0f}, empty in SQLite {int(c.sq.isna().sum())} cells"); assert dd.max() <= 2
nat_ex = EX.groupby(level="year").sum().sum(1); nat_c = NUM[""].groupby(level="year").sum().sum(1)
print("[99L2] district sum / national attendees:", (P.groupby("year").examinees.sum() / nat_ex).round(3).to_dict())
print("[99L2] district sum / national cases:", (P.groupby("year").cases.sum() / nat_c).round(3).to_dict())
cs = {suf: P.groupby("year")["cases" + suf].transform("sum").values for suf in OUTS}
rsc = lambda e, suf: e * cs[suf] / pd.Series(e).groupby(P.year.values).transform("sum").values
E = {suf: np.zeros(len(P)) for suf in OUTS}; EP = {suf: np.zeros(len(P)) for suf in OUTS}; EXA = 0; scs = []
for s in SEXES:
    X = P[["year", "key"]].merge(G[G.sex == s], on=["year", "key"], how="left", validate="one_to_one"); assert X.tot.notna().all(), X[X.tot.isna()][["year", "key"]]
    raw = X[BANDS].values * UPT.xs(s, level="sex").loc[X.year.values].values
    sc = S[("exam", s)].values / raw.sum(1); exam = raw * sc[:, None]; scs.append(sc); EXA = EXA + exam
    for suf in OUTS:
        E[suf] += (exam * RATE[suf].xs(s, level="sex").loc[X.year.values].values).sum(1)
        EP[suf] += (X[BANDS].values * (NUM[suf].xs(s, level="sex") / NATPOP.xs(s, level="sex")).loc[X.year.values].values).sum(1)
RATE_A = NUM[""].groupby(level="year").sum() / EX.groupby(level="year").sum()
e_age = (EXA * RATE_A.loc[P.year.values].values).sum(1)
for suf in OUTS:
    P["E_std" + suf] = rsc(E[suf], suf); P["E_pop" + suf] = rsc(EP[suf], suf)
    assert np.allclose(P.groupby("year")["E_std" + suf].sum(), P.groupby("year")["cases" + suf].sum())
P["E_std_age"] = rsc(e_age, "")
H = pd.DataFrame(rows80).groupby(["year", "key"], as_index=False)[["tot", "p80"]].sum(); H["pop80_share_raw"] = 100 * H.p80 / H.tot
# The published build stored this share in an intermediate CSV and read it back with the default pandas parser; the same
# text round trip is applied here so that the expected-count file is byte-identical (it changes at most the last digit).
H["pop80_share_raw"] = pd.read_csv(io.StringIO(H[["pop80_share_raw"]].to_csv(index=False))).pop80_share_raw.values
P = P.merge(H[["year", "key", "pop80_share_raw"]], on=["year", "key"], how="left", validate="one_to_one"); assert P.pop80_share_raw.notna().all()
nat = P.groupby("year").apply(lambda d: d.cases.sum() / d.examinees.sum()); P["E_crude"] = P.examinees * P.year.map(nat)
P["SIR_std"] = P.cases / P.E_std
P["uptake20"] = P.examinees / P[["year", "key"]].merge(G.groupby(["year", "key"], as_index=False)[BANDS[1:]].sum().assign(a20=lambda d: d[BANDS[1:]].sum(1))[["year", "key", "a20"]], on=["year", "key"], how="left", validate="one_to_one").a20.values
P["SIR_pop"] = P.cases / P.E_pop; P["SIR_crude"] = P.cases / P.E_crude
cols = ["year", "fbd_region", "examinees", "cases", "E_std", "E_std_age", "E_pop", "E_crude", "pop80_share_raw", "uptake20", "SIR_std", "SIR_pop", "SIR_crude"]
fp = os.path.join(PAN, f"{TAG}_Estd3.csv"); P[cols].to_csv(fp, index=False, encoding="utf-8-sig")
sc_all = np.concatenate(scs); r = P.E_std / P.E_crude
print(f"[99L2] {fp}: rows {len(P)}, years {P.year.min()}-{P.year.max()}, districts {P.fbd_region.nunique()}, sum of cases {int(P.cases.sum()):,}, sum of attendees {int(P.examinees.sum()):,}")
print(f"[99L2] E_std/E_crude {r.min():.3f}~{r.max():.3f} · E_pop/E_std {(P.E_pop/P.E_std).min():.3f}~{(P.E_pop/P.E_std).max():.3f} · Spearman(SIR_std,SIR_pop) {P.SIR_std.corr(P.SIR_pop, method='spearman'):.3f} · Spearman(SIR_std,SIR_crude) {P.SIR_std.corr(P.SIR_crude, method='spearman'):.3f}")
print(f"[99L2] rescaling factor {sc_all.min():.3f}~{sc_all.max():.3f} (P5 {np.quantile(sc_all,.05):.3f}, P95 {np.quantile(sc_all,.95):.3f}); uptake (attendees / population 20+) {P.uptake20.min():.3f}~{P.uptake20.max():.3f}")
