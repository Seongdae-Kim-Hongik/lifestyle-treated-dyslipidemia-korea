#!/usr/bin/env python3
# 38_build_Estd_all.py - expected counts by indirect standardization (shared helper).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.2, MIT license). See README.md (Pipeline) for how to run.
import os, re, sys, glob, json, importlib.util, struct, zlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location("m36", os.path.join(HERE, "36_build_national_agerates.py")); m36 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m36)
spec40 = importlib.util.spec_from_file_location("m40", os.path.join(HERE, "40_region_crosswalk.py")); m40 = importlib.util.module_from_spec(spec40); spec40.loader.exec_module(m40)
NFC = m36.NFC; AGES = m36.AGES
SRC = os.path.join(ROOT, "00_원천", "NHIS_전국_질병분류_연령")
FBDZIP = os.environ.get("ST_FBDZIP") or os.path.expandvars("$ST_DATA_ROOT") + "/기타/R_Studio/FBD_DATA_ZIP"
TAGS = ["PERIO", "INFECT", "ARTH", "HTN", "MENTAL", "DM", "LIVER", "BRCA", "GCA"]
DEF = {
    "PERIO": [("K00", "K01"), ("K03", "K08")], "INFECT": [("A00", "B99")], "ARTH": [("M00", "M19"), ("M22", "M25")], "HTN": [("I10", "I15")],
    "MENTAL": [("F00", "F99")], "DM": [("E10", "E14")], "LIVER": [("K70", "K77")], "BRCA": [("C50", "C50")], "GCA": [("C16", "C16")]}
DEF_TXT = {"PERIO": "K00-K01,K03-K08 (NHIS periodontal disease definition; K02 dental caries excluded)", "INFECT": "A00-B99", "ARTH": "M00-M19,M22-M25", "HTN": "I10-I15", "MENTAL": "F00-F99",
           "DM": "E10-E14", "LIVER": "K70-K77", "BRCA": "C50", "GCA": "C16"}

def hwp_text(path):
    b = open(path, "rb").read(); assert b[:8] == bytes.fromhex("D0CF11E0A1B11AE1")
    ss = 1 << struct.unpack_from("<H", b, 30)[0]; mss = 1 << struct.unpack_from("<H", b, 32)[0]
    nfat, dir0 = struct.unpack_from("<I", b, 44)[0], struct.unpack_from("<I", b, 48)[0]
    cutoff, mfat0 = struct.unpack_from("<I", b, 56)[0], struct.unpack_from("<I", b, 60)[0]
    difat0, ndifat = struct.unpack_from("<I", b, 68)[0], struct.unpack_from("<I", b, 72)[0]
    sec = lambda i: b[512 + i * ss:512 + (i + 1) * ss]
    difat = list(struct.unpack_from("<109I", b, 76)); d = difat0
    for _ in range(ndifat): v = struct.unpack("<%dI" % (ss // 4), sec(d)); difat += v[:-1]; d = v[-1]
    fat = []
    for i in difat[:nfat]: fat += struct.unpack("<%dI" % (ss // 4), sec(i))
    def chain(s):
        o = []
        while s < 0xFFFFFFFA: o.append(s); s = fat[s]
        return o
    read = lambda s: b"".join(sec(i) for i in chain(s))
    dd = read(dir0); ents = []
    for k in range(len(dd) // 128):
        e = dd[k * 128:(k + 1) * 128]; nl = struct.unpack_from("<H", e, 64)[0]
        ents.append((e[:max(nl - 2, 0)].decode("utf-16le"), e[66], struct.unpack_from("<I", e, 116)[0], struct.unpack_from("<Q", e, 120)[0]))
    mini = read(ents[0][2]); minifat = []
    for i in chain(mfat0): minifat += struct.unpack("<%dI" % (ss // 4), sec(i))
    def mread(s, z):
        o = b""
        while s < 0xFFFFFFFA: o += mini[s * mss:(s + 1) * mss]; s = minifat[s]
        return o[:z]
    def stream(nm):
        for n, t, s, z in ents:
            if n == nm and t == 2: return read(s)[:z] if z >= cutoff else mread(s, z)
    comp = stream("FileHeader")[36] & 1; out = []
    for nm in sorted([n for n, t, s, z in ents if n.startswith("Section") and t == 2], key=lambda n: int(n[7:])):
        data = stream(nm); data = zlib.decompress(data, -15) if comp else data; i = 0
        while i < len(data):
            h = struct.unpack_from("<I", data, i)[0]; tag = h & 0x3FF; size = (h >> 20) & 0xFFF; i += 4
            if size == 0xFFF: size = struct.unpack_from("<I", data, i)[0]; i += 4
            if tag == 67:
                raw = data[i:i + size]; t = ""; j = 0
                while j + 1 < len(raw):
                    c = struct.unpack_from("<H", raw, j)[0]
                    if c < 32 and c not in (9, 10, 13): j += 2 if c in (0, 10, 13, 24, 25, 26, 27, 28, 29, 30, 31) else 16; continue
                    t += chr(c); j += 2
                out.append(t)
            i += size
    return out
def ref_table(path):
    L = [l.strip() for l in hwp_text(path) if l.strip()]; idx = [i for i, l in enumerate(L) if re.fullmatch(r"\d{3}", l)]; rows = {}
    for k, i in enumerate(idx):
        seg = L[i + 1:(idx[k + 1] if k + 1 < len(idx) else len(L))]
        icd = "".join(s for s in seg if re.match(r"^[A-Z]\d\d", s)).replace(" ", "").rstrip(","); nm = " ".join(s for s in seg if not re.match(r"^[A-Z]\d\d", s))
        rows.setdefault(int(L[i]), (re.sub(r"\s+", " ", nm).strip(), icd))
    return rows
def icd_ranges(s):
    out = []
    for p in [x for x in s.split(",") if x]:
        a, _, b = p.partition("-"); out.append((a[:3], (b or a)[:3]))
    return out
def overlap(r, D):
    a, b = r
    if any(lo <= a and b <= hi for lo, hi in D): return "full"
    return "part" if any(not (b < lo or a > hi) for lo, hi in D) else "none"

def build_mapping():
    r19 = ref_table(os.path.join(SRC, "2019_298 질병분류참조표.hwp")); r20 = ref_table(os.path.join(SRC, "2020_298 질병분류참조표.hwp"))
    assert sorted(r19) == list(range(1, 299)) and sorted(r20) == list(range(1, 299))
    assert all(r19[c][1] == r20[c][1] for c in r19), "ICD codes differ between the 2019 and 2020 reference tables"
    import kosis_api as K
    meta = [x for x in K.table_meta("350", "TX_35001_A061", "ITM") if x.get("OBJ_ID") == "15350AF5"]
    assert meta[0]["ITM_NM"] == "총계" and len(meta) >= 299
    kn = {i: (meta[i]["ITM_ID"], re.sub(r"\s+", "", meta[i]["ITM_NM"])) for i in range(1, 299)}
    rows = []
    for c in range(1, 299):
        nm, icd = r20[c]; hg = lambda x: re.sub(r"[^가-힣]", "", re.sub(r"\([^()]*[A-Za-z][^()]*\)", "", x))
        same = hg(nm)[:6] == hg(kn[c][1])[:6]
        for T in TAGS:
            st = [overlap(r, DEF[T]) for r in icd_ranges(icd)]
            if all(s == "none" for s in st): continue
            inc = all(s == "full" for s in st)
            why = (f"reference-table ICD {icd} lies fully within the definition {DEF_TXT[T]}" if inc else
                   f"reference-table ICD {icd} only partly overlaps the definition -> excluded (codes outside the definition mixed in)")
            rows.append(dict(TAG=T, 질환정의_ICD=DEF_TXT[T], code298=c, kosis_itm_id=kn[c][0], kosis_명칭=kn[c][1], 참조표_명칭=nm, 참조표_ICD=icd,
                             명칭일치=same, 포함=inc, 판단근거=why))
    BND = {"PERIO": {180: "dental caries K02 - excluded because the NHIS periodontal definition (K00-K01, K03-K08) omits K02", 182: "other oral cavity, salivary glands and jaws K09-K14 - outside K08"},
           "ARTH": {202: "acquired deformities of limbs M20-M21 - the definition skips M20-M21", 204: "systemic connective tissue disorders M30-M36 (lupus, etc.) - outside the arthritis definition"},
           "INFECT": {250: "congenital infectious and parasitic diseases P35-P37 - infection by name but ICD chapter P (perinatal)", 251: "infections specific to the perinatal period P38-P39 - chapter P", 291: "asymptomatic HIV infection status Z21 - chapter Z", 292: "health hazards related to communicable diseases Z20,Z22-Z29 - chapter Z",
                      198: "infections of the skin and subcutaneous tissue L00-L08 - chapter L", 165: "acute pharyngitis and tonsillitis J02-J03 - respiratory chapter J", 168: "influenza J09-J11 - chapter J", 169: "pneumonia J12-J18 - chapter J"},
           "HTN": {237: "hypertensive disorders in pregnancy O10-O16 - chapter O"}, "DM": {111: "other endocrine, nutritional and metabolic E15-E35, etc. - outside E10-E14"},
           "LIVER": {63: "malignant neoplasm of liver and intrahepatic bile ducts C22 - liver cancer is chapter C", 38: "other viral hepatitis B15,B17-B19 - infectious disease chapter (in INFECT)", 37: "acute hepatitis B B16 - infectious disease chapter", 195: "cholelithiasis and cholecystitis K80-K81 - outside K77"},
           "BRCA": {91: "benign neoplasm of breast D24 - not malignant", 223: "disorders of breast N60-N64 - not malignant", 89: "carcinoma in situ of cervix D06 - not breast"},
           "GCA": {183: "gastric and duodenal ulcer K25-K27 - not malignant", 59: "malignant neoplasm of oesophagus C15", 65: "malignant neoplasms of other digestive organs C17,C23-C24,C26"},
           "MENTAL": {122: "Alzheimer disease G30 - nervous system chapter G (dementia F00-F03 is in 112)", 121: "Parkinson disease G20 - chapter G"}}
    for T, dd in BND.items():
        for c, why in dd.items():
            nm, icd = r20[c]
            rows.append(dict(TAG=T, 질환정의_ICD=DEF_TXT[T], code298=c, kosis_itm_id=kn[c][0], kosis_명칭=kn[c][1], 참조표_명칭=nm, 참조표_ICD=icd,
                             명칭일치=hg(nm)[:6] == hg(kn[c][1])[:6], 포함=False, 판단근거="boundary code excluded: " + why))
    M = pd.DataFrame(rows).sort_values(["TAG", "포함", "code298"], ascending=[True, False, True])
    M["용도"] = "for national age-specific reference rates (age profile) only - the sum of patients over detailed categories is not a count of persons, because a person treated in several categories is counted more than once; the level is matched to the observed counts by rescaling so that sum E_std = sum cases in each year"
    assert M["명칭일치"].all(), M[~M["명칭일치"]]
    assert not M[M["포함"]].duplicated(["TAG", "code298"]).any()
    def expand(D):
        s = set()
        for lo, hi in D:
            L0, L1 = lo[0], hi[0]
            for ch in range(ord(L0), ord(L1) + 1):
                a = int(lo[1:]) if chr(ch) == L0 else 0; z = int(hi[1:]) if chr(ch) == L1 else 99
                s |= {f"{chr(ch)}{n:02d}" for n in range(a, z + 1)}
        return s
    cover = {}
    for T in TAGS:
        cov = set()
        for icd in M[(M.TAG == T) & M["포함"]]["참조표_ICD"]: cov |= expand(icd_ranges(icd))
        cover[T] = sorted(expand(DEF[T]) - cov)
    return M, cover

def kosis_codes(codes):
    import kosis_api as K
    items, objs = K.meta_codes("350", "TX_35001_A061"); dz = objs["15350AF5"]; cmap = {dz[c]: c for c in codes}; out = []; kdiff = []
    for tbl, y0, y1 in (("TX_35001_A061", 2011, 2017), ("DT_35001_A0611", 2018, 2018)):
        parts = []
        for k in range(0, len(codes), 40):
            p = {"method": "getList", "orgId": "350", "tblId": tbl, "itmId": "16350AAB1", "prdSe": "Y", "startPrdDe": str(y0), "endPrdDe": str(y1), "format": "json", "jsonVD": "Y",
                 "objL1": "+".join(dz[c] for c in codes[k:k + 40]), "objL2": "15350AB300", "objL3": "ALL"}
            parts.append(pd.DataFrame(K._get(K.BASE + "/Param/statisticsParameterData.do", p)))
        d = pd.concat(parts); assert (d.ITM_ID == "16350AAB1").all() and (d.C2 == "15350AB300").all()
        d["code"] = d.C1.map(cmap); d["DT"] = pd.to_numeric(d.DT.replace("-", 0)); assert d.code.notna().all()
        assert sorted(d.PRD_DE.astype(int).unique()) == list(range(y0, y1 + 1)) and set(d.code) == set(codes), (tbl, sorted(set(codes) - set(d.code)))
        for (yr, code), g in d.groupby(["PRD_DE", "code"]):
            tot = g.loc[g.C3_NM.str.replace(" ", "").isin(["합계", "계"]), "DT"]
            ag = g[~g.C3_NM.str.replace(" ", "").isin(["합계", "계"])]
            if len(tot) == 0 and ag.DT.sum() == 0: tot = pd.Series([0.0]); kdiff.append((int(yr), int(code), "no total row and all ages 0 -> 0"))
            assert len(tot) == 1, (tbl, yr, code); dif = ag.DT.sum() - tot.iloc[0]
            assert abs(dif) <= max(20, 1e-3 * tot.iloc[0]), f"KOSIS {tbl} {yr} {code}: sum over ages {ag.DT.sum()} != total {tot.iloc[0]}"
            if dif: kdiff.append((int(yr), int(code), int(dif)))
            for nm, v in zip(ag.C3_NM, ag.DT): out.append((int(yr), int(code), m36.age10(int(re.findall(r"\d+", nm)[0])), float(v)))
            out.append((int(yr), int(code), "TOTAL", float(tot.iloc[0])))
        print(f"[38] KOSIS {tbl} {y0}-{y1}: {d.code.nunique()} codes, {d.C3_NM.nunique()-1} age groups")
    return out, kdiff
def excel_codes(codes):
    out = []
    for f in sorted(glob.glob(os.path.join(SRC, "*_298 질병분류.xlsx"))):
        yr = int(os.path.basename(f)[:4]); vals = m36.excel_year(f)
        assert sorted({c for c, _ in vals}) == list(range(1, 299))
        ages = sorted({a for _, a in vals if a != "TOTAL"}); assert len(ages) == 17
        for c in codes:
            s = sum(vals[(c, a)] for a in ages); assert s == vals[(c, "TOTAL")], f"{yr} {c}: sum over ages != total"
            for a in ages: out.append((yr, c, m36.age10(a), vals[(c, a)]))
            out.append((yr, c, "TOTAL", vals[(c, "TOTAL")]))
        print(f"[38] {yr} Excel: {len(codes)} codes, sum over ages = total checked")
    return out

def shares_total():
    a = pd.read_csv(m36.AGEPOP); a["region"] = a.region.map(NFC); a["age10"] = a.age10.map(NFC)
    a["share"] = a["pop"] / a.groupby(["region", "year"])["pop"].transform("sum")
    return a.pivot_table(index=["region", "year"], columns="age10", values="share")[AGES]
MATCH = {}
def shares_female(regions):
    fbd = set(regions); rows = []; unmatched = {}
    mk = pd.read_csv(os.path.join(ROOT, "02_패널", "시군구_마스터키.csv"), dtype=str); KEY2REG = {NFC(k): NFC(r) for k, r in zip(mk.key, mk.fbd_region)}
    SIDO = set(m40.SIDO_STD) - {"서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "제주도"}
    for y in range(2011, 2025):
        d = pd.read_csv(os.path.join(FBDZIP, f"{y}.csv"), encoding="cp949"); d.columns = [c.strip() for c in d.columns]
        assert list(d.columns[:6]) == ["행정구역별", "연령별", "시점", "전체", "여자", "남자"], d.columns
        sido = None; cur = {}
        for nm, ag, v in zip(d["행정구역별"].astype(str).str.strip(), d["연령별"].astype(str).str.strip(), d["여자"]):
            if nm == "전국": sido = None; continue
            if nm in SIDO:
                sido = nm
                if not nm.startswith("세종"): continue
            if sido is None: continue
            sg = nm.split("-", 1)[1] if "-" in nm else nm
            v = pd.to_numeric(str(v).replace(",", ""), errors="coerce")
            if pd.isna(v): continue
            key = m40.make_key(sido, sg); sd, s2 = key.split("|"); reg = KEY2REG.get(NFC(key), NFC(sd + s2))
            if reg not in fbd and s2 == "청원군" and sd == "충청북도": reg = NFC("충청북도청주시")
            if reg not in fbd and s2.endswith("군") and NFC(sd + s2[:-1] + "시") in fbd: reg = NFC(sd + s2[:-1] + "시")
            if reg not in fbd: unmatched[(y, sd + s2)] = 1; continue
            MATCH.setdefault((y, reg), set()).add(nm)
            cur.setdefault(reg, {}); cur[reg][ag] = cur[reg].get(ag, 0.0) + float(v)
        for reg, A in cur.items():
            if "계" not in A or A["계"] <= 0: continue
            five = {int(re.findall(r"\d+", k)[0]): x for k, x in A.items() if re.fullmatch(r"\d+-\d+세", k)}
            if not all(lo in five for lo in range(0, 70, 5)): continue
            p = [five[lo] + five[lo + 5] for lo in range(0, 70, 10)] + [A["계"] - sum(five[lo] for lo in range(0, 70, 5))]
            assert p[-1] >= 0; tot = A["계"]
            rows += [(reg, y, ag, x / tot, tot) for ag, x in zip(AGES, p)]
    S = pd.DataFrame(rows, columns=["region", "year", "age10", "share", "female_total"])
    return S.pivot_table(index=["region", "year"], columns="age10", values="share")[AGES], S.groupby(["region", "year"]).female_total.first(), unmatched
def agepop(P, W):
    rows, fb = [], []; regs = set(W.index.get_level_values(0))
    for r, y, off in zip(P.fbd_region, P.year, P.offset):
        if (r, y) in W.index: s = W.loc[(r, y)].values
        else:
            assert r in regs, f"no age shares: {r}"; ys = W.loc[r].index.values; src = int(ys[np.argmin(np.abs(ys - y))]); s = W.loc[(r, src)].values; fb.append((r, y, src))
        rows += [(y, r, ag, off * sh) for ag, sh in zip(AGES, s)]
    return pd.DataFrame(rows, columns=["year", "fbd_region", "age10", "pop"]), fb

if __name__ == "__main__":
    M, cover = build_mapping()
    M.to_csv(os.path.join(ROOT, "04_분석", "00_298코드_질환매핑.csv"), index=False, encoding="utf-8-sig")
    print("[38] codes included in the mapping:", {T: M[(M.TAG == T) & M["포함"]].code298.tolist() for T in TAGS})
    print("[38] partial overlap (excluded):", M[~M["포함"]][["TAG", "code298", "참조표_ICD"]].values.tolist())
    print("[38] 3-character ICD codes in the definition not covered by included codes (including codes not in the 298 list):", {T: v for T, v in cover.items() if v})
    CODES = {T: M[(M.TAG == T) & M["포함"]].code298.astype(int).tolist() for T in TAGS}
    assert CODES["MENTAL"] == list(range(112, 120)) and CODES["PERIO"] == [181] and CODES["ARTH"] == [200, 201, 203] and CODES["HTN"] == [145, 146] \
        and CODES["LIVER"] == [193, 194] and CODES["DM"] == [104] and CODES["BRCA"] == [73] and CODES["GCA"] == [60] and CODES["INFECT"] == list(range(1, 58))
    allc = sorted({c for v in CODES.values() for c in v})
    ko, kdiff = kosis_codes(allc)
    L = pd.DataFrame(ko + excel_codes(allc), columns=["year", "code", "age10", "patients"]).groupby(["year", "code", "age10"], as_index=False).patients.sum()
    print(f"[38] KOSIS differences between sum over ages and total (allowed, recorded): {kdiff if kdiff else 'none'}")
    A = L[L.age10 != "TOTAL"]; assert sorted(A.year.unique()) == list(range(2011, 2025))
    WT = shares_total(); WF = None; RATES = []; SUMMARY = []
    for T in TAGS:
        PAN = os.path.join(ROOT, "04_분석", T, f"panel_{T}.csv")
        P = pd.read_csv(PAN, encoding="utf-8-sig"); P["fbd_region"] = P.fbd_region.map(NFC)
        if T == "BRCA":
            WF, FT, um = shares_female(P.fbd_region.unique())
            FT.index.names = ["fbd_region", "year"]; chk = P.set_index(["fbd_region", "year"]).offset; j = chk.to_frame().join(FT, how="inner"); rr = (j.female_total / j.offset)
            print(f"[38] BRCA female age shares: district-years {WF.shape[0]}/{len(P)} matched; median ratio of FBD female total to panel offset {rr.median():.4f} (P1 {rr.quantile(.01):.3f}, P99 {rr.quantile(.99):.3f}; Cheongju 2011-13 is 1.22 with Cheongwon merged, Sejong is 2.0 because of duplicate source rows; no effect since only shares are used); unmatched names {len(um)} (abolished names, sub-districts of merged cities)")
            W = WF
        else: W = WT
        AP, fb = agepop(P, W)
        num = A[A.code.isin(CODES[T])].groupby(["year", "age10"]).patients.sum()
        den = AP.groupby(["year", "age10"])["pop"].sum()
        rate = (num / den).rename("rate").reset_index(); rate["TAG"] = T; rate["patients_sum"] = num.values; rate["denom_nat"] = den.reindex(num.index).values
        RATES.append(rate)
        X = AP.merge(rate[["year", "age10", "rate"]], on=["year", "age10"], how="left"); assert X.rate.notna().all()
        X["e"] = X["pop"] * X.rate; E = X.groupby(["year", "fbd_region"], as_index=False).e.sum()
        D = P[["year", "fbd_region", "cases", "E", "older_adult_share_raw"]].merge(E, on=["year", "fbd_region"], how="left", validate="one_to_one"); assert D.e.notna().all()
        D["E_std"] = D.e * D.groupby("year").cases.transform("sum") / D.groupby("year").e.transform("sum")
        assert (D.groupby("year").E_std.sum() - D.groupby("year").cases.sum()).abs().max() < 1e-6 * D.cases.sum()
        D["SIR_crude"] = D.cases / D.E; D["SIR_std"] = D.cases / D.E_std
        out = D[["year", "fbd_region", "E_std", "SIR_crude", "SIR_std"]]
        f = os.path.join(ROOT, "02_패널", f"{T}_Estd.csv")
        if T == "MENTAL":
            old = pd.read_csv(f, encoding="utf-8-sig"); old["fbd_region"] = old.fbd_region.map(NFC)
            cmp = old.merge(out, on=["year", "fbd_region"], suffixes=("_old", "_new")); rel = (cmp.E_std_new / cmp.E_std_old - 1).abs().max()
            print(f"[38] MENTAL reproduction check: {len(cmp)} rows, max relative difference in E_std {rel:.2e} (existing 02_패널/MENTAL_Estd.csv used as is)"); assert rel < 1e-6
        else:
            out.to_csv(f, index=False, encoding="utf-8-sig")
        G = D.groupby("fbd_region").agg(cases=("cases", "sum"), E=("E", "sum"), Es=("E_std", "sum"), old=("older_adult_share_raw", "mean"))
        rc, _ = spearmanr(G.cases / G.E, G.old); rs, _ = spearmanr(G.cases / G.Es, G.old)
        SUMMARY.append((T, CODES[T], len(fb), round(rc, 3), round(rs, 3), round(float((D.E_std / D.E).min()), 3), round(float((D.E_std / D.E).max()), 3)))
        print(f"[38] {T}: codes {CODES[T] if len(CODES[T]) < 10 else str(CODES[T][0])+'~'+str(CODES[T][-1])}, age shares substituted {len(fb)}, SIR-older-age rho crude {rc:+.3f} -> std {rs:+.3f}, E_std/E {SUMMARY[-1][5]}~{SUMMARY[-1][6]}")
    R = pd.concat(RATES); R["age10"] = pd.Categorical(R.age10, AGES, ordered=True)
    R.sort_values(["TAG", "year", "age10"])[["TAG", "year", "age10", "patients_sum", "denom_nat", "rate"]].to_csv(os.path.join(ROOT, "02_패널", "ALL_national_agerates_std.csv"), index=False, encoding="utf-8-sig")
    print("[38] saved: 02_패널/<TAG>_Estd.csv (8 files, existing MENTAL kept), 02_패널/ALL_national_agerates_std.csv, 04_분석/00_298코드_질환매핑.csv")
    print(R[R.year == 2024].pivot(index="age10", columns="TAG", values="rate").mul(1e3).round(2).to_string())
