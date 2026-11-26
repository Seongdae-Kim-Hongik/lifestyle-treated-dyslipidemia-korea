# numbers_lipt.py: reads every value in the LIPT manuscript from result CSVs.
#  No hand-typed values; consistency checked with assert. Usage: from numbers_lipt import load; N = load()
import os, glob, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.environ.get("LIPT_B", os.path.dirname(os.path.dirname(HERE))); RS = os.path.join(B, "results_std3")   # input directory from LIPT_B
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.environ.get("LIPT_PAN", os.path.join(ROOT, "02_패널"))
WIN = [("W1_2011-17", 2011, 2017), ("W2_2018-24", 2018, 2024)]
rd = lambda f, **k: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", **k)
EDU, IMS, MPA = "tertiary_educated_share", "im_specialists_per_100k", "moderate_pa_rate"
ROB = [IMS, EDU, MPA]
CAP = ("서울", "경기", "인천")
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))
COV = ["pop80_share", "urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", IMS, "screening_uptake", EDU, "obesity_rate",
       "high_risk_drinking_rate", "current_smoking_rate", "walking_practice_rate", MPA, "public_sports_facilities_per_100k", "basic_livelihood_rate", "single_person_household_share"]

# Internal-medicine specialist _raw is on the log1p scale -> tables use the original scale (per 100,000)
LOG1P = {IMS}
def ORIG(v, q): return np.expm1(q[f"{v}_raw"]) if v in LOG1P else q[f"{v}_raw"]
def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_LIPT_std3.csv")); N["n_rows"] = len(P); N["n_districts"] = P.fbd_region.nunique()
    assert (N["n_rows"], N["n_districts"]) == (3192, 228)
    E = pd.read_csv(os.path.join(PAN, "LIPT_Estd3.csv"))
    assert int(E.cases.sum()) == int(P.cases.sum()) and abs(E.examinees.sum() - P.offset.sum()) < 1
    N["cases_total"] = int(P.cases.sum()); N["exam_total"] = float(E.examinees.sum())
    y = E.groupby("year")[["examinees", "cases"]].sum(); popy = P.groupby("year").population.sum()
    N["exam_y"] = y.examinees.to_dict(); N["cases_y"] = y.cases.to_dict(); N["pos_y"] = (100 * y.cases / y.examinees).to_dict()
    N["upt_nat_y"] = (y.examinees / popy).to_dict()
    N["rho_std_pop"] = float(E[["SIR_std", "SIR_pop"]].corr(method="spearman").iloc[0, 1])
    N["estd_ecrude"] = (float((E.E_std / E.E_crude).min()), float((E.E_std / E.E_crude).max()))
    T1 = {}
    for wn, a, b in WIN + [("2011-2024", 2011, 2024)]:
        q = P[(P.year >= a) & (P.year <= b)]; e = E[(E.year >= a) & (E.year <= b)]
        sir = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), exam=float(e.examinees.sum()), pos=100 * q.cases.sum() / e.examinees.sum(),
                      sir_p10=sir.quantile(.1), sir_p90=sir.quantile(.9), sir_med=sir.median(),
                      cov={v: (ORIG(v, q).mean(), ORIG(v, q).std()) for v in COV})
    N["T1"] = T1
    # Spatial
    s6m = rd("S6_moran_year.csv"); N["moran_year_min"], N["moran_year_max"] = s6m.moran_I.min(), s6m.moran_I.max()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"] = r8.loc["pearson_residual_area_mean", "moran_I"]; N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); s6 = s6[s6.observed]; assert len(s6) == 228; N["rr_min"], N["rr_max"] = s6.RR.min(), s6.RR.max()
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["hot_capital"] = int(((s6["class"] == "hotspot") & s6.fbd_region.str.startswith(CAP)).sum())
    N["cold_capital"] = int(((s6["class"] == "coldspot") & s6.fbd_region.str.startswith(CAP)).sum())
    wm = rd("S4b_window_spatialRR.csv"); wm = wm[wm["class"] != "unobserved"]; N["win_hot"] = wm[wm["class"] == "hotspot"].groupby("window").size().to_dict(); N["win_cold"] = wm[wm["class"] == "coldspot"].groupby("window").size().to_dict()
    hs = {w: set(wm[(wm.window == w) & (wm["class"] == "hotspot")].fbd_region) for w in wm.window.unique()}; N["hot_all_windows"] = len(set.intersection(*hs.values()))
    cs = {w: set(wm[(wm.window == w) & (wm["class"] == "coldspot")].fbd_region) for w in wm.window.unique()}; N["cold_all_windows"] = len(set.intersection(*cs.values()))
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    N["ehsa"] = rd("S11_ehsa_summary.csv").set_index("category").n.to_dict()
    # Main model and multiverse
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role", "label_en", "P_gt1"]].to_dict("index")
    _pr = rd("S46b_lipt_mpa_precise.csv").iloc[0]; assert abs(_pr.IRR - N["main"][MPA]["IRR"]) < 0.0006 and _pr.hi < 1   # 88L2 refit: rounded upper bound 1.000 -> 0.9998
    N["main"][MPA].update(lo=float(_pr.lo), hi=float(_pr.hi))
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); N["n_cred_hyp"] = int(((m3.role == "hypothesis") & m3.cred).sum())
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index")
    N["n_robust"] = int(s7.robust.sum()); assert set(s7.index[s7.robust]) == set(ROB), s7.index[s7.robust].tolist()
    hb = open(os.path.join(B, "HM_best_LIPT_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0])
    N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0]); N["waic_rulebest"] = float(hb.split("S3_lipid_risk_factors(")[1].split(",")[0])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = nc[["IRR", "lo", "hi", "cred"]].to_dict("index")
    wi = rd("S4_window_IRR.csv"); N["win_irr"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, r.cred) for r in wi.itertuples()}
    it = rd("S4_interaction.csv"); N["n_win_int"] = int(it.cred.sum()); N["win_int_cov"] = it[it.cred]["cov"].tolist()
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    N["retention"] = rd("S41_retention_by_cov.csv").set_index("cov").to_dict("index"); N["rubin"] = rd("S41_noise_rubin.csv").set_index("cov").to_dict("index")
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index"); N["oos"] = rd("S41_oos2024.csv").iloc[0].to_dict()
    N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict(); N["varpart"] = rd("S42_variance_partition.csv").set_index("component").to_dict("index")
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in rd("S41_nco_detail.csv").itertuples()}
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, r.cred) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    lo = rd("S41_leaveout_ranges.csv"); N["leaveout"] = {(r[0], r[1]): (int(r[2]), int(r[3])) for r in lo[~lo["cov"].str.startswith("__")].itertuples(index=False)}
    so = rd("S10_offset_sensitivity_IRR.csv"); N["epop"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in so.itertuples()}
    N["sens_main"] = {}
    for v in ["s577", "s2", "s8"]:
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens_main"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    rs = rd("S50_region_slopes.csv"); N["region_slope"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in rs.itertuples()}
    N["region_dwaic"] = rs.groupby("covariate").dWAIC_vs_common.first().to_dict()
    # Reverse-direction post hoc tests (88L, S46)
    s46 = rd("S46_lipt_posthoc.csv"); N["s46"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in s46.itertuples()}
    # P5 and P5b (specialists per area) from S46c, refitted with specialist count / area (not a log1p-scale value times population)
    s46c = rd("S46c_lipt_posthoc_P5fix.csv")
    for r in s46c.itertuples(): N["s46"][(r.analysis.replace("_fix", ""), r.cov)] = (r.IRR, r.lo, r.hi, bool(r.cred))
    assert not N["s46"][("P5_per_area", "spec_per_km2_log")][3]
    # Treatment-suspicion gap (99L3, S50)
    N["gap"] = json.load(open(os.path.join(RS, "S50_lipt_suspect_gap_summary.json")))
    cv = rd("S5_covid.csv"); N["covid_nint"] = int(cv[(cv.term == "var_x_post") & cv.cred].shape[0])
    N["ims_pop80_r"] = float(np.corrcoef(P.im_specialists_per_100k_raw, P.pop80_share_raw)[0, 1])
    N["ims_urban_r"] = float(np.corrcoef(P.im_specialists_per_100k_raw, P.urban_population_share_raw)[0, 1])
    N["ims_phys_r"] = float(np.corrcoef(P.im_specialists_per_100k_raw, P.physicians_per_1000_raw)[0, 1])
    # Additional manuscript values (computed only from result CSVs and panels, no hand entry)
    from scipy.stats import kendalltau, spearmanr
    s6all = rd("S6_spatial_RR.csv", dtype={"sigungu_cd": str}); s6o = s6all[s6all.observed]
    N["n_hot_rr110"] = int(((s6o["class"] == "hotspot") & (s6o.RR >= 1.10)).sum()); N["n_cold_rr090"] = int(((s6o["class"] == "coldspot") & (s6o.RR <= 0.90)).sum())
    kt = kendalltau(s6m.year, s6m.moran_I); N["moran_year_tau"] = (float(kt[0]), float(kt[1])); N["moran_y"] = dict(zip(s6m.year, s6m.moran_I))
    eb = rd("S12c_yearly_EB_SIR.csv").groupby("fbd_region").ebSIR.mean(); rr_ = s6o.set_index("fbd_region").RR
    N["rho_resid_eb"] = float(spearmanr(rr_.values, eb.reindex(rr_.index).values)[0])
    N["persist_null"] = {k: float(pe.loc["2011-2024", k]) for k in ("perm_p", "poisson_p", "B")}
    # Within-region education component: SD of two-way centred deviations (standardized units) -> RR per within SD
    xe = P[["fbd_region", "year", EDU]].copy(); xe["w"] = xe[EDU] - xe.groupby("fbd_region")[EDU].transform("mean") - xe.groupby("year")[EDU].transform("mean") + xe[EDU].mean()
    N["edu_within_sd"] = float(xe.w.std()); _bw = N["bw"][EDU + "__within"]; N["edu_within_perSD"] = tuple(float(x ** N["edu_within_sd"]) for x in _bw[:3])
    # Treatment-suspicion Spearman bootstrap (2000 district resamples, seed 20261126)
    gp = rd("S50_lipt_suspect_gap.csv"); rng = np.random.default_rng(20261126); a_ = gp.SIR_lipt.values; b_ = gp.SIR_susp.values
    bs = [spearmanr(a_[i], b_[i])[0] for i in (rng.integers(0, len(gp), len(gp)) for _ in range(2000))]
    N["rho_ts_boot"] = (float(spearmanr(a_, b_)[0]), float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975)))
    N["E_min"] = float(P.E.min()); N["cases_min"] = int(P.cases.min())
    sp7 = rd("S7_multiverse_specs.csv"); N["mv_nvar"] = (int(sp7.nvar.min()), float(sp7.nvar.median()), int(sp7.nvar.max()), len(sp7))
    N["resid_moran_spec"] = rd("S50_resid_moran_by_spec.csv").set_index("spec").to_dict("index")
    _mt = pd.read_csv(os.path.join(B, "panel_META_LIPT_std3.csv"), encoding="utf-8-sig"); N["vif_max"] = float(_mt[_mt.role.isin(["forced", "candidate"])].vif_final.max()); assert abs(N["vif_max"] - 6.99) < 0.01   # Main model, 16 variables
    # Judgement-composition gate (judgement_gate/out, checked against 17 editions of the notice): national yearly table
    JG = os.environ.get("LIPT_JG", os.path.join(os.path.dirname(B), "judgement_gate", "out"))
    t2 = pd.read_csv(os.path.join(JG, "T02_전국_연도별_유질환자_이상지질혈증_성분.csv"), encoding="utf-8-sig").set_index("year")
    yoy = 100 * (t2.j_pct / t2.j_pct.shift(1) - 1)
    N["jg_yoy"] = yoy.dropna().to_dict(); N["jg_meas"] = t2.meas_share.to_dict(); N["jg_jm"] = t2.j_over_m.to_dict()
    N["jg_tsI"] = pd.read_csv(os.path.join(JG, "TS_draft_판정기준_연혁_이상지질혈증.csv"), encoding="utf-8-sig")
    N["jg_tsII"] = pd.read_csv(os.path.join(JG, "TS_draft_판정구성대조_전국연도.csv"), encoding="utf-8-sig")
    # Recompute the ratio and share columns from the raw counts in T02, so that each value is rounded once
    _ts = N["jg_tsII"].set_index("Year"); _r = t2.loc[_ts.index]
    _ts["Treated, % of attendees"] = (100 * _r.j / _r.den).round(2)
    _ts["Questionnaire: drug treatment for dyslipidaemia, % (N043)"] = (100 * _r.m / _r.den).round(2)
    _ts["Questionnaire: diagnosed dyslipidaemia, % (N043)"] = (100 * _r.d / _r.den).round(2)
    _ts["Judged/questionnaire-treated ratio"] = (_r.j / _r.m).round(3)
    _ts["Lipid panel measured / attendees (N071/N099)"] = (_r.tc_n / _r.den).round(3)
    _ts["Suspected dyslipidaemia, % of attendees (N104)"] = (100 * _r.s / _r.den).round(2)
    _ts["Suspected, % of lipid-measured"] = (100 * _r.s / _r.tc_n).round(2)
    _jp = _r.j / _r.den; _ts["Year-on-year change in treated share, %"] = (100 * (_jp / _jp.shift(1) - 1)).round(1)
    N["jg_tsII"] = _ts.reset_index(); N["jg_jpct_nat"] = (100 * t2.j / t2.den).to_dict()
    assert abs(N["jg_yoy"][2018] - 7.6) < 0.1 and len(N["jg_tsI"]) == 17
    # Additional fits (fits/X_*.csv from 91d_extra_fits_lipt.R): analysis name -> {covariate: (RR, lo, hi, cred)}
    XF = os.path.join(B, "results_extra", "fits"); N["xf"] = {}; N["xf_waic"] = {}
    for f in sorted(glob.glob(os.path.join(XF, "X_*.csv"))):
        d = pd.read_csv(f); k = os.path.basename(f)[2:-4]
        N["xf"][k] = {r["cov"]: (float(r.IRR), float(r.lo), float(r.hi), bool(r.cred)) for _, r in d.iterrows()}; N["xf_waic"][k] = float(d.WAIC.iloc[0])
    b145 = pd.read_csv(os.path.join(B, "results_extra", "B145_waic_repeat_pointwise_SE.csv"), encoding="utf-8-sig").set_index("fit")
    N["waic_refit_max"] = float(b145.refit_range_max_abs.max()); N["waic_forced_dr1"] = float(b145.loc["set_REF_forced_only", "dWAIC_vs_S1"]); N["waic_forced_se"] = float(b145.loc["set_REF_forced_only", "SE_pointwise_diff"])
    e84 = pd.read_csv(os.path.join(B, "results_extra", "E084_map_values_SIR_obs_fitted.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
    a84 = e84[e84.period == "2011-2024"]; N["e084"] = (float(a84.SIR_obs.min()), float(a84.SIR_obs.max()), float(a84.SIR_obs.median()), float(a84[["SIR_obs", "SIR_fitted"]].corr().iloc[0, 1]))
    # Regional slopes from refits of the two reference models (2 repeats, identical values); ΔWAIC relative to the reference model with lower WAIC
    XB = os.path.join(B, "results_extra")
    b146 = pd.read_csv(os.path.join(XB, "B146_region_slopes_two_baselines.csv"), encoding="utf-8-sig"); assert (b146.groupby(["covariate", "region"]).IRR.nunique() == 1).all()
    b1 = b146[b146.rep == 1]
    N["region_slope"] = {f"{r.covariate}__{r.region}": (float(r.IRR), float(r.lo), float(r.hi), bool(r.cred)) for r in b1.itertuples()}
    N["region_dwaic"] = b1.groupby("covariate").dWAIC_vs_min_baseline.first().to_dict(); N["region_cpo_fail"] = b1.groupby("covariate").cpo_fail_frac.first().to_dict()
    N["region_refit_range"] = b1.groupby("covariate").refit_range_baselines.first().to_dict()
    import re as _re
    _l91 = open(os.path.join(XB, "logs", "run_91C.log"), encoding="utf-8").read()
    N["region_base_waic"] = {k: float(_re.search(rf"{k}_r1\s+WAIC ([\d.]+)", _l91).group(1)) for k in ("rs_base_common", "rs_base_regionFE")}
    assert N["region_base_waic"]["rs_base_common"] < N["region_base_waic"]["rs_base_regionFE"] and set(b1.baseline_min_WAIC) == {"rs_base_common_r1"}
    # Table 1 crude and standardized rates (S22), age-specific rates (S21, national table), n of the two data sources
    s22 = pd.read_csv(os.path.join(XB, "S22_table1.csv"), encoding="utf-8-sig"); s22["year"] = s22.year.astype(str); N["s22"] = s22.set_index("year").to_dict("index")
    _yy = s22[s22.year.str.fullmatch(r"\d{4}")]
    N["dist_nat_pct"] = (float(100 * min((_yy.cases_228 / _yy.cases_national).min(), (_yy.examinees_228 / _yy.examinees_national).min())),
                         float(100 * max((_yy.cases_228 / _yy.cases_national).max(), (_yy.examinees_228 / _yy.examinees_national).max())))
    assert int(N["s22"]["2011-2024"]["cases_228"]) == N["cases_total"] and abs(N["s22"]["2011-2024"]["examinees_228"] - N["exam_total"]) < 1
    N["s21"] = pd.read_csv(os.path.join(XB, "S21_age_sex_rates_rateratio_by_period.csv"), encoding="utf-8-sig")
    assert int(N["s21"][N["s21"].period == "2011-2024"].cases.sum()) == int(N["s22"]["2011-2024"]["cases_national"])
    # Zero cells for internal-medicine specialists and 4 variants without +1
    N["ims_zero_cells"] = int((np.expm1(P[f"{IMS}_raw"]).round(6) == 0).sum())
    p1 = pd.read_csv(os.path.join(RS, "plus1_check", "plus1_fixed_all.csv")); alt = p1[~p1.variant.str.startswith("orig")]
    _hyp = set(N["main"]) - {"urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"}
    _cs = lambda d: frozenset(d[d.cred & d["cov"].isin(_hyp)]["cov"])
    N["plus1_variants"] = sorted(alt.variant.unique()); N["plus1_same_set"] = all(_cs(g) == frozenset(ROB) for _, g in alt.groupby("variant"))
    a_ = alt[alt["cov"] == IMS]; N["plus1_ims_range"] = (float(a_.IRR.min()), float(a_.IRR.max())); assert len(N["plus1_variants"]) == 4 and N["plus1_same_set"]
    # Residual Moran permutation count and seed (from 81_fit_inla.R)
    _r81 = open(os.path.join(os.path.dirname(B), "analysis_root", "01_스크립트", "81_fit_inla.R"), encoding="utf-8").read().split("\n")
    N["moran_perm"] = int(rd("S8_residual_moran.csv").set_index("quantity").loc["pearson_residual_area_mean", "nperm"])
    N["moran_resid_seed"] = int(_re.search(r"set\.seed\((\d+)\)", next(l for l in _r81 if "pra<-tapply" in l)).group(1))
    # Sensitivity of the year-jump scan threshold (panel tables)
    PV = os.path.join(os.path.dirname(B), "panel_checks", "tables")
    t2s = pd.read_csv(os.path.join(PV, "T02s_임계값민감도_변수요약.csv"), encoding="utf-8-sig"); N["jump_flags"] = t2s.groupby("set").n_flag.sum().to_dict()
    N["jump_flags_default"] = int(len(pd.read_csv(os.path.join(PV, "T02_연도급변_전수스캔_플래그.csv"), encoding="utf-8-sig"))); assert N["jump_flags"]["default_0.2_5_3"] == N["jump_flags_default"]
    X = N["xf"]
    assert not X["E_crude"][EDU][3] and X["E_crude"][EDU][0] < 1 and not X["add_out_of_area_care"][IMS][3] and X["add_out_of_area_care"]["out_of_area_care_share"][3]
    assert not X["D145_drop_boundary3"][IMS][3] and X["D145_drop_boundary3"][EDU][3] and X["nco_fires_per_10000_plus_road"]["fires_per_10000"][3] and X["nco_fires_per_10000_urban_rw2"]["fires_per_10000"][3]
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame))})
    print("hot_by_sido", N["hot_by_sido"]); print("cold_by_sido", N["cold_by_sido"]); print("ehsa", N["ehsa"]); print("win_hot", N["win_hot"], "win_cold", N["win_cold"])
    print("pos_y", {k: round(v, 2) for k, v in N["pos_y"].items()}, "upt", {k: round(v, 3) for k, v in N["upt_nat_y"].items()})
    print("KH WAIC", {k: v for k, v in N["s43_waic"].items() if "KH" in k}, "main", N["waic_main"]); print("ppc", N["ppc"]); print("win_int", N["win_int_cov"]); print("dwaic", N["region_dwaic"])
    print("KH I", {v: N["s43"][("KH_typeI", v)] for v in ROB}); print("leaveout", N["leaveout"]); print("varpart", {k: round(v["share_of_sum"], 3) for k, v in N["varpart"].items() if v["share_of_sum"] == v["share_of_sum"]})
