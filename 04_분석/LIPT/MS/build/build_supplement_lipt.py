# build_supplement_lipt.py: Supplementary Material (single-blind, American spelling; one file, Sections S1-S9 in order of first citation in the text) plus a separate STROBE checklist file.
#  Values only from result CSVs. Header = author surname + running title and page number (as in the manuscript). Tables S1..., Fig. S1.
import os, json, subprocess, shutil, tempfile, pandas as pd
from docx.shared import Cm
import content_manuscript_lipt as C
from shared_lipt import LABEL, GROUPS as _G
GROUPS = [("Lifestyle-related risk factors" if g == "Lipid risk factors" else g, v) for g, v in _G]
from build_manuscript_lipt import TX, TITLE as DTITLE, foot_row, read_draft, supmarks
from american import amer as brit
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.environ.get("LIPT_OUT") or os.path.join(MSD, "out"); SUF = os.environ.get("LIPT_SUFFIX", ""); B = os.environ.get("LIPT_B", os.path.dirname(MSD)); RS = os.path.join(B, "results_std3")
N = C.N
SOFFICE = os.environ.get("SOFFICE") or shutil.which("soffice") or shutil.which("libreoffice")
f3 = lambda t: f"{t[0]:.3f} ({t[1]:.3f}–{C.fh(t[2]) if (len(t) > 3 and t[3]) else f'{t[2]:.3f}'})"
B1 = "Intervals with a bound shown as 1.000 were classified from unrounded values."
ROBV = [C.EDU, C.IMS, C.MPA]
SH = {C.EDU: "Tertiary education", C.IMS: "Internal-medicine specialists per 100,000 residents", C.MPA: "Moderate-to-vigorous activity"}
J = TX(cite="bracket", lines=False, sz=10); J.cell_ls = 2.0   # No line numbers in the supplement; table cell line spacing = 2x font size
_NB = [False]
def TF(title, header, rows, foot="", fs=8):   # Supplementary tables fixed at 8 pt
    header, rows, foot = supmarks(header, rows, foot)   # Footnote symbols -> superscript a, b, c
    title = brit(title); header = [brit(h) for h in header]; rows = [[brit(x) for x in r] for r in rows]
    (None if _NB[0] else J.page_break()); _NB[0] = False; J.table_fit(title, header, rows, "", fs_max=fs)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Supplementary Material</b>"); J.para(f"Manuscript: {DTITLE}")
TT = {'S1': 'Table S1. Dyslipidaemia judgement criteria in the 17 versions of the Health Screening Implementation Standards in force in 2011–2024', 'S2': 'Table S2. National counts of judged treated dyslipidaemia compared with questionnaire answers, lipid testing and suspected dyslipidaemia, 2011–2024', 'S3': 'Table S3. Descriptive statistics, data sources and years, expected direction, filled cells and supporting references for the 16 district-level covariates, 2011–2024', 'S4': 'Table S4. Panel checks with rules, thresholds and their basis, flags and actions', 'S5': 'Table S5. Robustness of the 3 subset-stable covariates', 'S6': 'Table S6. Negative-control exposures, changes in credibility in space–time models, multiplicity and model checks', 'S7': 'Table S7. STROBE checklist with the RECORD extension items for this ecological study of routinely collected data', 'S8': 'Table S8. Districts that were covariate-adjusted residual hot or cold spots in 2011–2024 or in either calendar window, by province', 'S9': 'Table S9. Rate ratios for the hypothesis covariates by calendar window and interactions with the window and with the COVID-19 period', 'S10': 'Table S10. Examination of internal-medicine specialist density, associated against its expected direction', 'S11': 'Table S11. National age- and sex-specific rates of treated dyslipidaemia among attendees by calendar window'}
SECT = [("Section S1. Supplementary methods and screening judgement criteria", ["S1", "S2"]), ("Section S2. Covariates", ["S3"]), ("Section S3. Panel checks before modelling", ["S4"]),
        ("Section S4. Robustness, comparison outcomes and model checks", ["S5", "S6"]), ("Section S5. STROBE and RECORD checklist", ["S7"]), ("Section S6. Persistence of the district pattern", ["S8", "FS1", "FS2"]),
        ("Section S7. Calendar windows and the COVID-19 period", ["S9"]), ("Section S8. Post hoc analyses", ["S10"]), ("Section S9. Age- and sex-specific rates", ["S11"]), ("Abbreviations", [])]
FT = {"FS1": "Fig. S1. Emerging hot spot analysis and calendar windows of residual hot and cold spots", "FS2": "Fig. S2. Observed and fitted sex- and age-standardised treatment ratios"}
def _toc(text, ind):   # Supplementary index: one line per item, 10 pt, single spacing, hanging indent
    pp = J.para(text, double=False, before=(0 if ind else 3)); pf = pp.paragraph_format; pf.left_indent = Cm(0.6 + (0.6 if ind else 0)); pf.first_line_indent = Cm(-0.6)
J.para("<b>Contents</b>", before=6)
for _h, _ks in SECT:
    _toc(_h, False)
    for _k in _ks: _toc(FT[_k] if _k.startswith("F") else TT[_k], True)
_LK = C._LK; _MT = pd.read_csv(os.path.join(B, "panel_META_LIPT_std3.csv"), encoding="utf-8-sig").set_index("variable")
_imp = lambda v: int(_MT.loc[v, "n_imputed_interp"] + _MT.loc[v, "n_imputed_sgg_mean"] + _MT.loc[v, "n_imputed_year_mean"])
# S1
_T1 = N["T1"]; _eh = N["ehsa"]; _pn = N["persist_null"]
SM = [("Outcome and denominator.", f"The national statistics portal publishes, for each year, the number of general health screening attendees and the number placed in each judgement category by district, sex and 5-year age group. Attendees who report a physician diagnosis of dyslipidaemia and current drug treatment are placed in the existing-disease category for dyslipidaemia; attendees with abnormal lipid results and no treatment are placed in the suspected-disease category. District sums of attendees and of treated dyslipidaemia were {N['dist_nat_pct'][0]:.1f}–{N['dist_nat_pct'][1]:.1f}% of national totals in every year. Seven district-years missing in the disease-by-district table were filled from the sum of the sex-by-age table for the same district and year. Sejong appears in the source tables only as a province-level row, with values for 2012–2024, and not as a district row; it was excluded from the analysis and kept only in the neighbourhood graph (Table S4), leaving {N['n_districts']} districts and {N['n_rows']:,} district-years."),
      ("Screening judgement criteria.", "The 17 versions of the Health Screening Implementation Standards in force in 2011–2024 were obtained from the national legislation portal, and the dyslipidaemia rows of the judgement tables were converted and checked twice against the originals (Table S1). The existing-disease criterion was the same sentence in every version and contained no laboratory threshold. The thresholds for suspected dyslipidaemia were lower in 2014–2015. From 2018 the lipid panel was restricted to men aged 24 years or older and women aged 40 years or older every 4 years, and the history question changed from a tick grid to a yes/no item for each condition. National counts of judged treated attendees were compared with questionnaire answers on diagnosis and drug treatment for dyslipidaemia, the components from which the judgement is made, and with the share of attendees who had a lipid panel (Table S2). The judged count did not exceed the questionnaire count of drug treatment in most sex and age strata from 2018; the ratio of the two fell in 2018 among people aged 45–59 years, and in 2011–2012 it was lower than in later years. Because the criterion did not change, these shifts are described as apparent changes in the programme judgement."),
      ("Standardisation.", f"Expected numbers E = Σ(attendees in sex s and age a) × (national share treated in s and a), with 15 age groups (19 years or younger, 5-year groups from 20–24 to 80–84 years, and 85 years or older), computed separately for each year and rescaled to the national number treated in that year, so that national changes over time are absorbed by E. The ratio of standardised to crude expected numbers ranged from {N['estd_ecrude'][0]:.2f} to {N['estd_ecrude'][1]:.2f}. A resident-based alternative applied the same national shares to the resident population; its district ratios correlated with the attendee-based ratios at Spearman's ρ {N['rho_std_pop']:.2f}."),
      ("Lipid-testing schedule.", f"The national share treated rose through 2018 without a fall ({N['jg_jpct_nat'][2017]:.2f}% in 2017, {N['jg_jpct_nat'][2018]:.2f}% in 2018), although its annual increase was smaller in 2018 than in other years (Table S2), and the calendar windows (2011–2017, 2018–2024), fixed before any covariate model was fitted, do not cross the change."),
      ("Covariates.", "Community Health Survey indicators are age-standardised district estimates. Specialist density counts internal-medicine specialists working in the district. Uptake is the share of people invited to general screening who attended. Basic livelihood security rates are official recipient counts of the Ministry of Health and Welfare divided by the resident population; they replaced the source-table values, which had collapsed or been inflated in 2021–2023 for 11 cities divided into general districts (417 district-years changed in all, mostly from the 2018 and 2024 official revisions). Comparison outcomes (patients treated for gastric cancer and for infectious disease, national health insurance statistics) and negative-control exposures (hit-and-run traffic accidents, fires per 10,000 residents, household waste recycling rate; Statistics Korea) covered 2011–2024. "
       f"Specialist density was 0 in {N['ims_zero_cells']} district-years, so it entered the models as log(1 + specialists per 100,000). The added constant was kept because 4 alternatives without it (interpolating the 2 isolated zeros between positive years, adding half the smallest positive value instead of 1, treating zeros as missing and filling them, and entering untransformed density) gave the same set of credible hypothesis covariates, with specialist RRs of {N['plus1_ims_range'][0]:.3f}–{N['plus1_ims_range'][1]:.3f}."),
      ("Models.", f"Software: R version 4.6.0 (R Foundation for Statistical Computing, Vienna, Austria) with the INLA (R-INLA), sf, spdep, Matrix, jsonlite, dplyr, ggplot2 and patchwork packages; Python 3.9 (Python Software Foundation, Wilmington, DE, USA) with pandas, NumPy, SciPy, GeoPandas and Matplotlib for data preparation, emerging hot spot analysis, persistence statistics and figures. "
       f"Model: log μ_it = log E_it + α + Σ β_k x_kit + b_i + γ_t + δ_t, where μ_it is the expected count in district i and year t, E_it the expected number, x_kit the standardised covariates, b_i the BYM2 district effect, γ_t a first-order random walk and δ_t independent year effects; exp(β_k) is the RR per 1 SD. "
       f"Negative binomial likelihood, chosen because its widely applicable information criterion (WAIC) for the forced-controls model ({_LK['nbinomial']:,.1f}) was lower than that of the Poisson model ({_LK['poisson']:,.1f}). District effect: BYM2 on an audited 593-edge contact graph of 229 districts with island districts linked to the nearest mainland district; penalised-complexity priors P(σ > 0.5) = 0.01 and P(φ < 0.5) = 2/3; year effects with penalised-complexity precision priors P(σ > 0.5) = 0.01; fixed effects with normal priors of mean 0 and precision 4 (intercept precision 0.001). "
       f"Covariate subsets: each of the {C.NHYP} hypothesis covariates was included with probability 0.5 until 200 distinct subsets were drawn (seed 20261019), and every subset model kept the 5 forced controls. "
       f"The covariate set was fixed in advance; a smaller lifestyle-risk-factor set had a slightly lower WAIC ({N['waic_rulebest']:,.1f} vs {N['waic_main']:,.1f}) and gave the same results for lifestyle-related risk factors (no credible association except an inverse one for moderate-to-vigorous activity). Regions for region-specific slopes: Capital (Seoul, Incheon, Gyeonggi), Chungcheong, Honam, Yeongnam and Gangwon–Jeju. "
       "The 44 alternative fits were: forced controls smoothed; Poisson with an observation-level effect; second-order random-walk and first-order autoregressive year effects; a province-by-year effect; Spatial+-type adjustment; unlagged fits restricted to the lag years; 1-year and 2-year lags; leave-one-province and leave-one-year fits; winsorised extreme values; 3-year moving-average survey covariates; and even and odd years. "
       f"Moran's I was tested with 999 permutations (seed 1), which assume that district values are exchangeable under the null hypothesis of no spatial autocorrelation."),
      ("Persistence.", f"Kendall's W was computed from annual rankings of observed (unsmoothed) district ratios and compared with {int(_pn['B']):,} permutations of the rankings within each year and {int(_pn['B']):,} Poisson simulations that keep each district's expected numbers, the population-size-preserving null model. Emerging hot spot analysis used empirical Bayes-smoothed annual ratios."),
      ("Post hoc sensitivity analyses.", "Added after the principal results were known (Table S5): crude expected numbers (attendees multiplied by the national crude share of each year); expected numbers from fixed 2015 national sex–age shares or with the shares at ages 75 years or older raised or lowered by 10%; exclusion of the 3 districts whose territory or province changed (Cheongju, Gongju, Gunwi) and of 4 further districts with name or status changes; addition of the share of patients treated outside their district of residence (National Health Insurance Service regional medical-use statistics), clinics per 100,000 or care institutions per 100,000; refits without 2020–2021, from 2015 or without filled cells; Beta(1, 1) and Jeffreys priors for the BYM2 mixing parameter; replacement of self-reported obesity, which the data dictionary lists as possibly dependent on the outcome, by the screening-based share of attendees advised on weight management (the principal model keeps survey-based obesity); and a restricted spatial regression constraining the district effect to be orthogonal to district-mean covariates, which is known to understate uncertainty and is shown without interpretation."),
      ("Variance shares.", "The share of each linear-predictor component is its variance divided by the variance of the full linear predictor. Components are correlated, so the shares do not sum to 100%."),
      ("Treated versus suspected dyslipidaemia.", "Suspected dyslipidaemia used the suspected-disease category of the same screening programme, standardised in the same way within each window because its thresholds were lower in 2014–2015 and only about one-third of attendees had a lipid panel from 2018. District ratios were pooled over 2011–2024; G, the log of the treated ratio over the suspected ratio, was tested for spatial autocorrelation with Moran's I (999 permutations). The 95% interval for Spearman's ρ came from 2,000 bootstrap resamples of districts (seed 20261126)."),
      ("Post hoc analyses.", "The decomposition into district means and two-way-centred deviations was planned. After the principal results were seen, specialist density, associated against its expected direction, was examined with a single-covariate model, removal of physician density, tertiary education, or physician density and urban share, one-way decomposition into district means and deviations, addition of unmet need and the shares of attendees treated for hypertension or diabetes, and replacement by, or addition of, log specialists per km².")]
J.page_break(); J.head("Section S1. Supplementary methods and screening judgement criteria", 2)
for h, t in SM: J.para(f"<b>{h}</b> {t}")
# Table S1 history of the judgement criteria, Table S2 judgement-composition check
import re as _re
def _thr(x):
    x = str(x).strip(); m = _re.match(r"^(\d+) 이상$", x)
    if m: return "≥" + m.group(1)
    m = _re.match(r"^(\d+) 미만$", x)
    return "<" + m.group(1) if m else x
def _date(x):
    y, m_, d_ = [int(v) for v in _re.findall(r"\d+", str(x))[:3]]; return f"{y}-{m_:02d}-{d_:02d}"
TS1 = N["jg_tsI"]; assert TS1["유질환자_판정기준"].nunique() == 1
rows = []
for r in TS1.itertuples(index=False):
    no = _re.sub(r"^제|호", "", str(r[0])).replace("(전부개정)", " (full revision)"); yr = int(_date(r[1])[:4]); new = yr >= 2018
    rows.append([no, _date(r[1]), _thr(r.TC_질환의심), _thr(r.HDL_질환의심), _thr(r.TG_질환의심), _thr(r.LDL_질환의심), "Restricted*" if new else "All", "Yes/no†" if new else "Grid"])
assert not any(_re.search(r"[가-힣]", c) for r_ in rows for c in r_)
J.para("")
TF(TT["S1"], ["Notice", "In force from", "TC", "HDL-C", "TG", "LDL-C", "Lipid panel", "History item"], rows,
   "Ministry of Health and Welfare notices; thresholds for suspected dyslipidaemia in mg/dL. TC, total cholesterol; HDL-C, high-density lipoprotein cholesterol; TG, triglycerides; LDL-C, low-density lipoprotein cholesterol. In every version, existing disease was defined as attendees judged to have hypertension, diabetes, dyslipidaemia or pulmonary tuberculosis and currently taking medication, without a laboratory threshold. Lipid panel, attendees eligible for the lipid panel; history item, format of the medical-history question on diagnosis and treatment (grid, one tick grid for all conditions). *Men aged 24 years or older and women aged 40 years or older, every 4 years. †Separate yes/no item for each condition. Each row was converted from the original table and checked against an independent second extraction.")
_NB[0] = True
TS2 = N["jg_tsII"]; c_ = list(TS2.columns)
fmt = lambda v, d: "" if pd.isna(v) else (f"{int(v):,}" if d == 0 else f"{v:.{d}f}")
rows = [[str(int(r[c_[0]])), fmt(r[c_[3]], 2), fmt(r[c_[4]], 2), fmt(r[c_[6]], 3), fmt(r[c_[7]], 3), fmt(r[c_[8]], 2), fmt(r[c_[9]], 2), fmt(r[c_[12]], 1) or "NA"] for _, r in TS2.iterrows()]
TF(TT["S2"], ["Year", "Treated (judged), %", "Treated (history), %", "Judged / history", "Lipid panel / attendees", "Suspected, %", "Suspected, % of tested", "Annual change, %"], rows,
   "Percentages are of attendees unless stated. Treated (judged), existing-disease judgement for dyslipidaemia; treated (history), questionnaire answer on current drug treatment for dyslipidaemia; judged / history, ratio of judged to questionnaire-treated attendees; lipid panel / attendees, attendees with a lipid panel over all attendees (above 1 in 2015–2017 because some were counted only in lipid tables); suspected, suspected-disease judgement; annual change, change in the judged share from the previous year; NA, not applicable. Source: national screening tables of the Korean Statistical Information Service.")
# S2 covariates (Table S3) with a supporting-reference column (main-text reference numbers, already-cited keys only)
import build_manuscript_lipt as _BJ
_Jm, _rl, _ = _BJ.build(); _REFN = {k: i + 1 for i, k in enumerate(_Jm.cites)}
EVK = {"im_specialists_per_100k": ["guagliardo2004spatial", "kim2017evaluation"], "screening_uptake": ["park2021association", "yun2023socioeconomic"], "tertiary_educated_share": ["marcus2021unmet"],
       "obesity_rate": ["dattilo1992effects"], "high_risk_drinking_rate": ["brien2011effect"], "current_smoking_rate": ["craig1989cigarette"],   # Keys with supporting references
       "walking_practice_rate": ["kodama2007effect"], "moderate_pa_rate": ["kodama2007effect", "smart2025effect"], "public_sports_facilities_per_100k": ["kodama2007effect", "smart2025effect"],
       "basic_livelihood_rate": ["wallachkildemoes2013adherence", "ashworth2007social"], "single_person_household_share": ["park2022multi"],
       "urban_population_share": ["park2016spatial", "lee2025national"], "physicians_per_1000": ["park2016spatial"], "sex_ratio": ["lee2025national"], "fiscal_independence": ["park2022multi"], "pop80_share": ["lee2025national"]}
assert all(k in _REFN for v in EVK.values() for k in v) and set(EVK) == set(LABEL)   # Supporting references for all 16 covariates
def _ev(v):
    ks = EVK.get(v)
    return ", ".join(str(n) for n in sorted(_REFN[k] for k in ks))
J_SETS = json.load(open(os.path.join(B, "sets_LIPT_std3.json"), encoding="utf-8"))
DIRN = {k: v.split()[0].replace("-", "−") for k, v in J_SETS["expected_direction"].items()}
MAPV = {_MT.loc[v, "source_column"]: v for v in _MT.index}
DIR = {MAPV[k]: d for k, d in DIRN.items() if k in MAPV}
from shared_lipt import SRCEN, UNIT, SRCAB, YRAB, SRC_FOOT
from numbers_lipt import ORIG
_P = pd.read_csv(os.path.join(B, "panel_LIPT_std3.csv"))
def _d(x): return 0 if abs(x) >= 100 else (2 if abs(x) < 1 else 1)
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs:
        m = _MT.loc[v]; x = ORIG(v, _P); q1, md, q3 = x.quantile([.25, .5, .75]); k = _d(md)
        rows.append([f"  {LABEL[v]}", UNIT[v], (f"{SRCAB[v]}, {YRAB.get(v, '2011–24')}").replace(", ", ",\u00a0").replace("–", "\u2060–\u2060"), f"{md:,.{k}f} ({q1:,.{k}f}⁠–⁠{q3:,.{k}f})", f"{x.min():,.{k}f}⁠–⁠{x.max():,.{k}f}", ("NA" if m.role == "forced" else DIR[v]), f"{_imp(v):,}", _ev(v)])
assert sum(1 for r in rows if r[0] != "__H__") == 16 and all(DIR.get(v) for g, vs in GROUPS[:-1] for v in vs)
J.page_break(); J.head("Section S2. Covariates", 2); _NB[0] = True
# Table S3: separate median and range cells (fewer line breaks)
J.fit_pad = 0.4
TF(TT["S3"], ["Covariate", "Unit", "Source, years", "Median (IQR)", "Range", "Sign", "Filled", "Ref."], rows,
   f"IQR, interquartile range; NA, not applicable (no direction specified for forced controls). {SRC_FOOT} †Census years 2010, 2015 and 2020, interpolated between censuses and held at 2020 thereafter. ‡Age-standardised district estimates. §Not surveyed in 2019 (obesity) or 2018 (moderate-to-vigorous activity). Statistics are over all {N['n_rows']:,} district-years on the original scale (specialists entered the models as log(1 + specialists per 100,000)). Filled, district-years filled by within-district interpolation, district mean or year mean, out of {N['n_rows']:,}. Sign, expected direction of the association; Ref., numbers in the reference list of the manuscript for the evidence behind the expected direction or, for forced controls, behind their inclusion; for public sports facilities the evidence concerns the physical activity they support, and for single-person households the cited survey found higher screening participation, so the expected direction rests on the assumption stated in the Methods.")
J.fit_pad = 0.65
# S3 panel checks (Table S4), Sejong row
J.page_break(); J.head("Section S3. Panel checks before modelling", 2); _NB[0] = True
_jf = N["jump_flags"]; _v5 = _MT[_MT.role.isin(["forced", "candidate"]) & (_MT.vif_final >= 5)].index.tolist(); assert _v5 == ["pop80_share"], _v5
rows = [["Twofold year means", "Largest/smallest positive yearly mean ≥2", "Separates a shift of a whole year from district noise; series data-gate rule", "Outcome and expected numbers (national share treated rose 1.7% to 12.6%); standardised columns with yearly means near 0", "Real trend absorbed by yearly national shares; retained"],
        ["Year-to-year jumps", "<0.2 or >5 times the mean of adjacent years; ≥3-fold single-year spike, step or end-year change", "Larger than sampling variation of small-area estimates; a 3-fold step marks a change of definition or source table", f"{N['jump_flags_default']:,} cells: survey estimates in small counties, public sports facilities (9), specialists (1), negative-control and unmet-need rates", "Checked against source tables; real changes, retained"],
        ["Missing source years", "No observation in a year", "Structural absence of a source table", "Single-person households before 2015", "Filled with district means; perturbation sensitivity"],
        ["Ratio above 100", "Maximum >100 for a rate or ratio", "A percentage cannot exceed 100", "Sex ratio (men per 100 women)", "Retained (definition)"],
        ["Missing district-years", "No observation", "Any gap", f"{sum(json.load(open(os.path.join(RS, 'S41_imputed_cells.json'))).values()):,} cells", "Filled within districts; perturbation sensitivity"],
        ["Outcome reconstruction", "District sums equal national totals", "Coverage of the national count", f"{N['dist_nat_pct'][0]:.1f}–{N['dist_nat_pct'][1]:.1f}% of national totals in all 14 years; 7 blank cells filled from sex-by-age sums", "None"],
        ["Unobserved district", "No district row in the source tables", "Outcome not published", "Sejong (Sejong Special Self-Governing City), province-level row only (2012–2024)", "Kept in the neighbourhood graph, excluded from the likelihood; no data in maps"],
        ["Source ≠ official count", "Panel value ≠ official recipient count", "Official count is the reference", "Basic livelihood security, 417 cells", "Replaced by official count ÷ resident population"],
        ["Collinearity", "Variance inflation factor ≥10", "Conventional limit", f"None (maximum {N['vif_max']:.2f}, share aged 80+)", "None"]]
TF(TT["S4"], ["Check", "Threshold", "Basis", "Flags in this panel", "Action"], rows, f"Checks were run on the analytic panel ({N['n_rows']:,} district-years) before any covariate model was fitted. "
   f"Threshold sensitivity: with stricter jump thresholds (<1/3 or >3 times adjacent years and 2-fold changes) the scan flagged {_jf['stricter_0.33_3_2']:,} cells and with looser ones (<0.1 or >10 times and 4-fold) {_jf['looser_0.1_10_4']:,}, against {_jf['default_0.2_5_3']:,}; the additional cells were small-county survey estimates, small counts and the early rise of the outcome, no threshold led to a correction, and the only correction (basic livelihood security) did not depend on a threshold, so the analytic panel and the results were the same under all 3 sets. With a variance inflation limit of 5 instead of 10, only the share aged 80 years or older, a forced control, would be flagged.")
# S4 robustness (Table S5)
LO = N["leaveout"]
def rrow(lab, fn): return [lab] + [fn(v) for v in ROBV]
RG = ("Capital", "Chungcheong", "Honam", "Yeongnam", "Gangwon_Jeju")
rows = [["__H__", "Covariate selection and specification"],
        rrow("  Subsets credible / same sign, %", lambda v: f"{100*N['mv'][v]['cred_frac']:.0f} / {100*N['mv'][v]['sign_agree']:.0f}"),
        rrow(f"  Alternative fits retained (of {N['retention'][C.EDU]['n_specs']})", lambda v: f"{N['retention'][v]['kept']}/{N['retention'][v]['n_specs']}"),
        rrow("  Leave-one-province retained", lambda v: f"{LO[('province', v)][1]}/{LO[('province', v)][0]}"),
        rrow("  Leave-one-year retained", lambda v: f"{LO[('year', v)][1]}/{LO[('year', v)][0]}"),
        rrow("  Perturbed filled values, pooled RR", lambda v: f"{N['rubin'][v]['IRR_pooled']:.3f} ({N['rubin'][v]['lo']:.3f}–{N['rubin'][v]['hi']:.3f})"),
        rrow("  Perturbed filled values, credible fits of 20", lambda v: f"{N['rubin'][v]['n_cred']}"),
        rrow("  1-year lagged covariates", lambda v: f3(N["s41"][("E1_lag1", v)])),
        rrow("  2-year lagged covariates", lambda v: f3(N["s41"][("E2_lag2", v)])),
        rrow("  Age-only expected numbers (sex not standardised)", lambda v: f3(N["sens_main"]["s8"][v])),
        rrow("  Share aged 80+ omitted", lambda v: f3(N["sens_main"]["s2"][v])),
        rrow("  Queen contiguity graph", lambda v: f3(N["sens_main"]["s577"][v])),
        rrow("  Expected numbers from residents", lambda v: f"{N['epop'][v][0]:.3f} ({N['epop'][v][1]:.3f}–{N['epop'][v][2]:.3f})"),
        rrow("  Spatial+ adjustment", lambda v: f3(N["s41"][("D1_spatial_plus", v)])),
        ["__H__", "Spatial structure"],
        rrow("  No district effect", lambda v: f3(N["s43"][("no_spatial", v)])),
        rrow("  Intrinsic CAR district effect only", lambda v: f3(N["s43"][("icar_besag", v)])),
        ["__H__", "Space–time interactions"],
        rrow("  Knorr-Held type I", lambda v: f3(N["s43"][("KH_typeI", v)])),
        rrow(f"  Knorr-Held type II (ΔWAIC {C.dW('KH_typeII'):,.0f})", lambda v: f3(N["s43"][("KH_typeII", v)])),
        rrow(f"  Knorr-Held type III (ΔWAIC {C.dW('KH_typeIII'):,.0f})", lambda v: f3(N["s43"][("KH_typeIII", v)])),
        rrow(f"  Knorr-Held type IV (ΔWAIC {C.dW('KH_typeIV'):,.0f})", lambda v: f3(N["s43"][("KH_typeIV", v)])),
        ["__H__", "Decompositions"],
        rrow("  District mean, two-way (planned)", lambda v: f3(N["bw"][v + "__between"])),
        rrow("  Within-district deviation, two-way (planned)", lambda v: f3(N["bw"][v + "__within"])),
        rrow("  District mean, one-way (post hoc)", lambda v: f3(N["s46"][("P4_between_within", v + "__B")]) if v == C.IMS else "NA"),
        rrow("  Within-district deviation, one-way (post hoc)", lambda v: f3(N["s46"][("P4_between_within", v + "__W")]) if v == C.IMS else "NA"),
        ["__H__", "Comparison outcomes"],
        rrow("  Gastric cancer care", lambda v: f3(N["nco"][("GCA", v)])),
        rrow("  Infectious disease care", lambda v: f3(N["nco"][("INFECT", v)])),
        ["__H__", "Region-specific slopes"]] + [rrow(f"  {r.replace('_', '–')}", lambda v, r=r: "Unstable*" if v == C.EDU else f3(N["region_slope"][f"{v}__{r}"])) for r in RG] + [
        rrow("  ΔWAIC vs lower-WAIC baseline (common slopes)", lambda v: f"{N['region_dwaic'][v]:+.1f}" + ("*" if v == C.EDU else "")),
        rrow("  Baseline WAIC, common slopes / with region main effects", lambda v: f"{N['region_base_waic']['rs_base_common']:,.1f} / {N['region_base_waic']['rs_base_regionFE']:,.1f}"),
        rrow("  CPO failures, % of observations", lambda v: f"{100*N['region_cpo_fail'][v]:.0f}"),
        rrow("  WAIC range over 2 refits of the baselines", lambda v: f"{N['region_refit_range'][v]:.1f}"),
        ["__H__", "Post hoc sensitivity analyses"],
        rrow("  Crude expected numbers", lambda v: f3(N["xf"]["E_crude"][v])),
        rrow("  Expected numbers from fixed 2015 shares", lambda v: f3(N["xf"]["E_fix2015"][v])),
        rrow("  Shares at ages 75+ raised by 10%", lambda v: f3(N["xf"]["E_75p_plus10"][v])),
        rrow("  Shares at ages 75+ lowered by 10%", lambda v: f3(N["xf"]["E_75p_minus10"][v])),
        rrow("  Three districts with territorial change excluded", lambda v: f3(N["xf"]["D145_drop_boundary3"][v])),
        rrow("  Seven districts with any boundary or name change excluded", lambda v: f3(N["xf"]["D145_drop_boundary7"][v])),
        rrow("  Out-of-district care share added", lambda v: f3(N["xf"]["add_out_of_area_care"][v])),
        rrow("  Clinics per 100,000 added", lambda v: f3(N["xf"]["add_clinics_per_100k"][v])),
        rrow("  Care institutions per 100,000 added", lambda v: f3(N["xf"]["add_care_institutions_per_100k"][v])),
        rrow("  2020–2021 excluded", lambda v: f3(N["xf"]["years_drop_2020_21"][v])),
        rrow("  2015–2024 only", lambda v: f3(N["xf"]["years_from_2015"][v])),
        rrow("  Filled cells removed", lambda v: f3(N["xf"]["obsonly_all3"][v])),
        rrow("  Beta(1, 1) prior for mixing parameter", lambda v: f3(N["xf"]["prior_phi_beta11"][v])),
        rrow("  Jeffreys prior for mixing parameter", lambda v: f3(N["xf"]["prior_phi_jeffreys"][v])),
        rrow("  Screening-based obesity proxy", lambda v: f3(N["xf"]["S1b_obesity_screening_proxy"][v])),
        rrow("  Restricted spatial regression (not interpreted)", lambda v: f3(N["xf"]["D199_RSR"][v])),
        ["__H__", "Unmeasured confounding"],
        rrow("  E-value, point / CrI limit", lambda v: f"{N['evalue'][v]['E_point']:.2f} / {N['evalue'][v]['E_limit']:.2f}")]
J.page_break(); J.head("Section S4. Robustness, comparison outcomes and model checks", 2); _NB[0] = True
TF(TT["S5"], ["Analysis"] + [SH[v] for v in ROBV], rows,
   "Values are rate ratios (RRs) per 1 standard deviation with 95% credible intervals (CrIs) unless stated. Retained, credible with the principal-model sign. Alternative fits are listed in Section S1. "
   "Spatial+ adjustment, covariates replaced by their residuals after removing spatially smooth components. Restricted spatial regression, district effect constrained to be orthogonal to district-mean covariates; it understates uncertainty and is not interpreted. CAR, conditional autoregressive. WAIC, widely applicable information criterion; ΔWAIC, difference in WAIC from the principal model (negative values indicate better fit); type I is an observation-level effect and was not compared by WAIC. "
   "Two-way decomposition, district means and deviations centred on both district and year means; one-way decomposition, deviations from district means only (fitted for specialist density only; NA, not fitted). Region-specific slopes, RRs per 1 standard deviation within each region, from a model with region-specific slopes for that covariate; ΔWAIC is the difference from the lower-WAIC of 2 baselines (common slopes; common slopes with region main effects), read as support for heterogeneity at −6 or less, weak support from −6 to −4, no detectable difference from −4 to 4 and favouring common slopes above 4 (thresholds set after the principal results were known); CPO, conditional predictive ordinate. *The region-specific model for tertiary education fitted much worse than the baselines and was unstable, so its regional RRs are not estimable and are not shown. "
   "E-value, the minimum strength of association, on the RR scale, that an unmeasured confounder would need with both the covariate and the outcome to explain away the estimate (point) or the CrI limit closer to 1. " + B1)
NCN = {"hit_and_run_rate": "Hit-and-run accidents", "fires_per_10000": "Fires per 10,000", "waste_recycling_rate": "Household waste recycling"}
SPN = {"principal": "Principal model", "forced_only": "Forced controls only", "parsimonious": "Smaller covariate set", "no_spatial": "No district effect", "iid_district": "Independent district effect only", "icar_district": "Intrinsic CAR district effect only", "typeI_interaction": "Knorr-Held type I interaction"}
RMS = N["resid_moran_spec"]; assert set(RMS) == set(SPN)
_MI = lambda k: (N['moran_resid'], N['moran_resid_p']) if k == 'principal' else (RMS[k]['resid_moran_I'], RMS[k]['p_perm'])   # Main-model row = the same main-model estimates as in the main text
rows = [["__H__", "Negative-control exposures (added one at a time), RR (95% CrI)"]] + [[f"  {NCN[k]}", f"{v['IRR']:.3f} ({v['lo']:.3f}–{v['hi']:.3f})"] for k, v in N["negctl"].items()]
rows += [["  Fires, with road paving added", f3(N["xf"]["nco_fires_per_10000_plus_road"]["fires_per_10000"])], ["  Fires, urban share modelled non-linearly", f3(N["xf"]["nco_fires_per_10000_urban_rw2"]["fires_per_10000"])]]
_KHN = {"KH_typeI": "Type I", "KH_typeII": "Type II", "KH_typeIII": "Type III", "KH_typeIV": "Type IV"}; _khr = []
for _a, _an in _KHN.items():
    for _v in N["main"]:
        _t = N["s43"].get((_a, _v))
        if _t is not None and bool(_t[3]) != bool(N["main"][_v]["cred"]):
            _khr.append([f"  {_an}, {LABEL[_v][0].lower() + LABEL[_v][1:]}" + (" (forced)" if N["main"][_v]["role"] == "forced" else ""), f3(_t) + ("; became credible" if _t[3] else "; no longer credible")])
assert any("became credible" in r[1] for r in _khr)
rows += [["__H__", "Knorr-Held space–time models, covariates whose credibility differed from the principal model, RR (95% CrI)"]] + _khr
rows += [["__H__", f"Multiplicity, {C.NHYP} hypothesis covariates at the 95% level"],
         ["  Credible associations expected by chance, principal model", f"{C.EXP_CHANCE:.2f} (observed {N['n_cred_hyp']})"],
         ["  Credible window interactions expected by chance", f"{C.EXP_CHANCE:.2f} (observed {N['n_win_int']})"]]
rows += [["__H__", "Predictive checks"], ["  95% posterior predictive coverage, %", f"{100*N['ppc']['coverage95']:.1f}"], ["  50% posterior predictive coverage, %", f"{100*N['ppc']['coverage50']:.1f}"],
         ["  PIT Kolmogorov–Smirnov <i>P</i>", "<0.001" if N['ppc']['pit_ks_p'] < 0.001 else f"{N['ppc']['pit_ks_p']:.3f}"], ["  Held-out 2024 coverage (95%), %", f"{100*N['oos']['coverage95']:.1f}"],
         ["__H__", "Residual Moran's I (two-sided permutation <i>P</i>)"]] + [[f"  {SPN[k]}", f"{_MI(k)[0]:.2f} ({'<0.001' if _MI(k)[1] < 0.001 else format(_MI(k)[1], '.3f')})"] for k in SPN] + [
         ["__H__", "Share of linear-predictor variance, %"],
         ["  Structured spatial effect", f"{100*N['varpart']['spatial_structured']['share_of_linear_predictor_var']:.1f}"],
         ["  All covariates, including forced controls", f"{100*N['varpart']['fixed_covariates']['share_of_linear_predictor_var']:.1f}"],
         ["  Hypothesis covariates", f"{100*N['varpart']['fixed_hypothesis']['share_of_linear_predictor_var']:.1f}"]]
TF(TT["S6"], ["Analysis", "Result"], rows, f"RR, rate ratio per 1 standard deviation; CrI, credible interval; PIT, probability integral transform; CAR, conditional autoregressive. Residual Moran's I used district means of Pearson residuals with {N['moran_perm']} permutations (seed {N['moran_resid_seed']}); the principal-model row is from the principal fit reported in the manuscript, and the other rows from fits of each specification. Variance shares are the variance of each linear-predictor component divided by the variance of the full linear predictor; components are correlated, so the shares are not additive and do not sum to 100%.")
# S5 STROBE + RECORD
MH = [h for h, _ in C.METHODS]; RH = [h for h, _ in C.RESULTS]; assert MH[0].startswith("Design") and MH[2] == "Covariates" and RH[0].startswith("Treated")
M_ = lambda *i: "Methods, " + " and ".join(str(x) for x in i); R_ = lambda *i: "Results, " + " and ".join(str(x) for x in i)
CK = [("Title and abstract", "1", "Title; Abstract"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"), ("Study design", "4", M_(1)), ("Setting", "5", M_(1)),
      ("Participants", "6", M_(1) + " (district aggregates; ecological)"), ("Variables", "7", M_(2, 3) + "; Section S2; Table 1; Table S3"), ("Data sources/measurement", "8", "Methods; Section S1; Tables S1 and S2"),
      ("Bias", "9", M_(5) + "; Sections S3, S4 and S8"), ("Study size", "10", M_(1) + f" ({N['n_districts']} districts)"), ("Quantitative variables", "11", M_(3)),
      ("Statistical methods", "12", M_(4, 5)), ("Participants (flow)", "13", "Not applicable (aggregate district data)"), ("Descriptive data", "14", R_(1) + "; Table 1"), ("Outcome data", "15", R_(1)),
      ("Main results", "16", R_(2, 3) + "; Table 2; Fig. 1"), ("Other analyses", "17", "Results, 4–6; Fig. 2; Sections S4 and S6–S8"),
      ("Key results", "18", "Discussion, Principal findings"), ("Limitations", "19", "Discussion, Strengths and limitations"), ("Interpretation", "20", "Discussion"), ("Generalisability", "21", "Discussion, Strengths and limitations"),
      ("Funding", "22", "Statements and Declarations, Funding statement"),
      ("RECORD: type of data in title or abstract", "1.1", "Abstract, Methods (national health screening statistics)"), ("RECORD: region and time frame in title or abstract", "1.2", "Title; Abstract, Methods"),
      ("RECORD: linkage of databases", "1.3", "Not applicable (district tables merged by district code; no individual linkage)"), ("RECORD: selection of the population", "6.1", M_(1) + "; Section S1; Table S1"),
      ("RECORD: validation of codes or algorithms", "6.2", "Discussion, Strengths and limitations (validation of self-report); Table S2"), ("RECORD: linkage flow", "6.3", "Not applicable"),
      ("RECORD: codes and algorithms for variables", "7.1", M_(1, 3) + "; Sections S1 and S2; Tables S1 and S3"), ("RECORD: access to the database", "12.1", M_(1) + " (published aggregate statistics); Statements and Declarations, Data availability"),
      ("RECORD: data cleaning", "12.2", "Section S3; Table S4"), ("RECORD: linkage methods", "12.3", "Not applicable"), ("RECORD: selection of included units", "13.1", "Section S1 (coverage of national totals); Table S4"),
      ("RECORD: limitations of routinely collected data", "19.1", "Discussion, Strengths and limitations"), ("RECORD: access to protocol, data and code", "22.1", "Statements and Declarations, Data availability")]
J.page_break(); J.head("Section S5. STROBE and RECORD checklist", 2); _NB[0] = True
TF(TT["S7"], ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK],
   "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology; RECORD, REporting of studies Conducted using Observational Routinely collected health Data.")
# S6 persistence: text (Kendall W = ranks of observed ratios), Table S8 district list, Fig. S1
J.page_break(); J.head("Section S6. Persistence of the district pattern", 2)
J.para(f"The 10th–90th percentile range of district treatment ratios was {_T1['W1_2011-17']['sir_p10']:.2f}–{_T1['W1_2011-17']['sir_p90']:.2f} in 2011–2017 and {_T1['W2_2018-24']['sir_p10']:.2f}–{_T1['W2_2018-24']['sir_p90']:.2f} in 2018–2024. "
       f"The window models identified {N['win_hot']['W1_2011-17']} hot and {N['win_cold']['W1_2011-17']} cold spots in 2011–2017 and {N['win_hot']['W2_2018-24']} hot and {N['win_cold']['W2_2018-24']} cold spots in 2018–2024; {N['hot_all_windows']} districts were hot spots and {N['cold_all_windows']} cold spots in both (Table S8; Fig. S1B). "
       f"Kendall's W of annual district rankings of observed ratios was {N['kendall_W']:.2f}; it exceeded every value from the permutation and Poisson null models ({int(_pn['B']):,} each; <i>P</i> < 0.001). "
       f"Emerging hot spot analysis classified {_eh['Persistent hot']} districts as persistent, {_eh['Consecutive hot']} as consecutive, {_eh['Intensifying hot']} as intensifying and {_eh['Diminishing hot']} as diminishing hot spots, and {_eh['Persistent cold']} as persistent, {_eh['Consecutive cold']} as consecutive and {_eh['Sporadic cold']} as sporadic cold spots; {_eh['No pattern']} districts showed no pattern, and the remaining districts fell into other categories (Fig. S1A).")
NM = pd.read_csv(os.path.join(HERE, "district_names_en.csv"), encoding="utf-8").set_index("fbd_region").name_en
import unicodedata as _ud
_nf = lambda x: _ud.normalize("NFC", str(x)).strip()
S6R = pd.read_csv(os.path.join(RS, "S6_spatial_RR.csv"), dtype={"sigungu_cd": str}); S6R = S6R[S6R.observed].copy(); S6R["fr"] = S6R.fbd_region.map(_nf)
WMR = pd.read_csv(os.path.join(RS, "S4b_window_spatialRR.csv"), dtype={"sigungu_cd": str}); WMR["fr"] = WMR.fbd_region.map(_nf)
wcl = {w: WMR[WMR.window == w].set_index("fr")["class"] for w in ("W1_2011-17", "W2_2018-24")}
CL = {"hotspot": "Hot", "coldspot": "Cold"}
S6R["w1"] = S6R.fr.map(wcl["W1_2011-17"]); S6R["w2"] = S6R.fr.map(wcl["W2_2018-24"])
S6R = S6R[S6R["class"].isin(CL) | S6R.w1.isin(CL) | S6R.w2.isin(CL)].copy()
S6R["sido"] = S6R.fr.str.extract(r"^(\S+?(?:도|시))")[0]; S6R["prov"] = S6R.sido.map(C.EN); assert S6R.prov.notna().all()
S6R["en"] = S6R.fr.map(NM); assert S6R.en.notna().all()
porder = list(dict.fromkeys(S6R.sort_values("sido").prov))
rows = []
for pv in sorted(porder):
    sub = S6R[S6R.prov == pv].sort_values(["RR"], ascending=False); rows.append(["__H__", f"{pv} ({len(sub)})"])
    for _, r in sub.iterrows(): rows.append([f"  {r.en}", f"{r.RR:.2f} ({r.lo:.2f}–{r.hi:.2f})", CL.get(r["class"], "–"), CL.get(r.w1, "–"), CL.get(r.w2, "–")])
nh_ = sum(1 for r in rows if r[0] != "__H__" and r[2] == "Hot"); nc_ = sum(1 for r in rows if r[0] != "__H__" and r[2] == "Cold")
nb_h = sum(1 for r in rows if r[0] != "__H__" and r[3] == "Hot" and r[4] == "Hot"); nb_c = sum(1 for r in rows if r[0] != "__H__" and r[3] == "Cold" and r[4] == "Cold")
assert (nh_, nc_, nb_h, nb_c) == (N["n_hot"], N["n_cold"], N["hot_all_windows"], N["cold_all_windows"]), (nh_, nc_, nb_h, nb_c)
_NB[0] = True
TF(TT["S8"], ["District", "Residual RR (95% CrI), 2011–2024", "2011–2024", "2011–2017", "2018–2024"], rows,
   f"RR, residual spatial rate ratio from the principal model (posterior mean of the exponentiated Besag–York–Mollié 2 district effect); CrI, credible interval. Hot, posterior probability that the residual spatial RR exceeded 1 above 0.95; cold, below 0.05; –, neither. Window columns are from the principal model fitted to each window. Numbers in parentheses are districts listed. Totals: {N['n_hot']} hot and {N['n_cold']} cold spots in 2011–2024; {N['hot_all_windows']} hot and {N['cold_all_windows']} cold spots in both windows. Districts are sorted by residual RR within provinces; official English names.")
J.page_break(); _pp = J.para(""); _pp.alignment = 1   # Page break only at the start of the figure section
from docx.shared import Pt as _Pt
from docx.enum.text import WD_LINE_SPACING as _LS
_pp.paragraph_format.line_spacing_rule = _LS.SINGLE; _pp.paragraph_format.space_before = _Pt(6); _pp.paragraph_format.space_after = _Pt(6)   # Figure paragraph: single spacing, centred, 120 twips before and after
_pp.add_run().add_picture(os.path.join(HERE, "figs", "FigS1.png"), width=Cm(15.9))   # Text width <= 15.92 cm, equal to the 159 mm canvas (no scaling)
_lg = J.para("<b>Fig. S1.</b> (A) Emerging hot spot analysis (Getis–Ord Gi* statistics with Mann–Kendall trend tests) of empirical Bayes-smoothed treatment ratios, 2011–2024; all categories are listed, with numbers of districts in parentheses. (B) Number of calendar windows (2011–2017, 2018–2024) in which each district was a covariate-adjusted residual hot or cold spot in the principal model; numbers of districts in parentheses. In both panels, no data, Sejong, published only as a province-level row; the bar shows 0, 50 and 100 km and the triangle points north.")
for _r in _lg.runs:
    if _r.bold: _r.font.size = _Pt(11)   # Figure caption title 11 pt, caption 10 pt
_lg.paragraph_format.line_spacing_rule = _LS.SINGLE; _lg.paragraph_format.space_before = _Pt(10); _lg.paragraph_format.space_after = _Pt(3)   # Single spacing
_e84 = N["e084"]
J.page_break(); _p2 = J.para(""); _p2.alignment = 1; _p2.paragraph_format.line_spacing_rule = _LS.SINGLE; _p2.paragraph_format.space_before = _Pt(6); _p2.paragraph_format.space_after = _Pt(6)
_p2.add_run().add_picture(os.path.join(HERE, "figs", "FigS2.png"), width=Cm(15.9))
_lg = J.para(f"<b>Fig. S2.</b> (A) Observed sex- and age-standardised treatment ratio (observed over expected numbers) and (B) fitted ratio from the principal model (fitted over expected numbers) by district, 2011–2024, in the 6 fixed classes of Fig. 1A. Observed ratios ranged from {_e84[0]:.2f} to {_e84[1]:.2f} (median {_e84[2]:.2f}) and correlated with the fitted ratios at r {_e84[3]:.2f}. The covariate-adjusted residual ratio is mapped in Fig. 1A of the manuscript. No data, Sejong, published only as a province-level row; the bar shows 0, 50 and 100 km and the triangle points north.")
for _r in _lg.runs:
    if _r.bold: _r.font.size = _Pt(11)   # Figure caption title 11 pt, caption 10 pt
_lg.paragraph_format.line_spacing_rule = _LS.SINGLE; _lg.paragraph_format.space_before = _Pt(10); _lg.paragraph_format.space_after = _Pt(3)   # Single spacing
# S7 windows (Table S9)
WI = pd.read_csv(os.path.join(RS, "S4_window_IRR.csv")).set_index(["cov", "window"]); IT = pd.read_csv(os.path.join(RS, "S4_interaction.csv")).set_index("cov")
CV = pd.read_csv(os.path.join(RS, "S5_covid.csv")); CVX = CV[CV.term == "var_x_post"].set_index("cov")
rows = []
for g, vs in GROUPS[:-1]:
    rows.append(["__H__", g])
    for v in vs: rows.append([f"  {LABEL[v]}"] + [f3(tuple(WI.loc[(v, w), ["IRR", "lo", "hi", "cred"]])) for w in ("W1_2011-17", "W2_2018-24")] + [f3(tuple(IT.loc[v, ["IRR_ratio", "lo", "hi", "cred"]])), f3(tuple(CVX.loc[v, ["IRR", "lo", "hi", "cred"]]))])
J.page_break(); J.head("Section S7. Calendar windows and the COVID-19 period", 2); _NB[0] = True
TF(TT["S9"], ["Covariate", "2011–2017", "2018–2024", "Ratio, later vs earlier window", "Interaction, 2020 onwards"], rows,
   "Rate ratio per 1 standard deviation (95% credible interval). Window columns: principal model structure fitted separately to each window with all forced controls. Ratio: window interaction in a single model (rate ratio in 2018–2024 divided by that in 2011–2017). Interaction, 2020 onwards: ratio of the rate ratio from 2020 onwards to that before 2020 (COVID-19 period). " + B1)
# S8 post hoc (Table S10); one-sided decomposition in Table S5
V = C.IMS; S46 = N["s46"]
rows = [["Principal model", f3((N["main"][V]["IRR"], N["main"][V]["lo"], N["main"][V]["hi"], True))],
        ["Unmet need and treated hypertension and diabetes added", f3(S46[("P1_plus_access_dx", V)])],
        ["Single covariate with forced controls", f3(S46[("P2_alone", V)])],
        ["Physician density removed", f3(S46[("P3a_drop_physicians", V)])],
        ["Tertiary education removed", f3(S46[("P3b_drop_tertiary", V)])],
        ["Physician density and urban share removed", f3(S46[("P3c_drop_physicians_urban", V)])],
        ["Specialists per km² (log) replacing per population", f3(S46[("P5_per_area", "spec_per_km2_log")])],
        ["Per population, with per km² added", f3(S46[("P5b_both", V)])],
        ["Per km² (log), with per population added", f3(S46[("P5b_both", "spec_per_km2_log")])]]
rows += [["__H__", "Region-specific slopes (per population)"]] + [[f"  {r.replace('_', '–')}", f3(N["region_slope"][f"{V}__{r}"])] for r in RG]
J.page_break(); J.head("Section S8. Post hoc analyses", 2); _NB[0] = True
TF(TT["S10"], ["Analysis", "RR (95% CrI)"], rows,
   f"RR, rate ratio per 1 standard deviation; CrI, credible interval. Expected direction positive. All rows except the principal model and the region-specific slopes were added after the results were seen; the one-way decomposition is in Table S5. Specialists per population correlated with the share aged 80 years or older (r {N['ims_pop80_r']:.2f}), urban share (r {N['ims_urban_r']:.2f}) and physician density (r {N['ims_phys_r']:.2f}).")
# S9 age- and sex-specific rates: national table, per 100,000 examinees
S21 = N["s21"]; _ab = list(dict.fromkeys(S21.age_band)); assert len(_ab) == 15
_rt = S21.set_index(["sex", "age_band", "period"]).rate_per100k
_AL = lambda a: "19 or younger" if a == "0-19" else ("85 or older" if a == "85+" else a.replace("-", "–"))
_PR = ("2011-2017", "2018-2024", "2011-2024")
rows = [[f"{_AL(a)}"] + [f"{_rt[(sx, a, pr)]:,.0f}" for sx in ("남자", "여자") for pr in _PR] for a in _ab]
J.page_break(); J.head("Section S9. Age- and sex-specific rates", 2)
_pk = {sx: max(_ab, key=lambda a: _rt[(sx, a, "2011-2024")]) for sx in ("남자", "여자")}; _up = [a for a in _ab if all(_rt[(sx, a, "2018-2024")] > _rt[(sx, a, "2011-2017")] for sx in ("남자", "여자"))]
assert _up == _ab[1:], _up
J.para(f"National rates of treated dyslipidaemia among attendees over 2011–2024 rose with age to a peak at {_AL(_pk['남자'])} years in men and {_AL(_pk['여자'])} years in women and were lower at older ages; they were higher in 2018–2024 than in 2011–2017 in every age group from {_AL(_ab[1])} years in both sexes (Table S11). The oldest age group is open-ended, so ageing within it can raise its rate without any change in treatment at a given age.")
_NB[0] = True
TF(TT["S11"], ["Age, years", "Men, 2011⁠–⁠2017", "Men, 2018⁠–⁠2024", "Men, 2011⁠–⁠2024", "Women, 2011⁠–⁠2017", "Women, 2018⁠–⁠2024", "Women, 2011⁠–⁠2024"], rows,
   "Attendances with treated dyslipidaemia per 100,000 attendances, from the national tables by sex and age group (DT_35007_N106 and DT_35007_N099) that supplied the national shares for indirect standardisation; these tables include Sejong.")
# Abbreviation list
J.page_break(); J.head("Abbreviations", 2)
J.para("BYM2, Besag–York–Mollié 2; CAR, conditional autoregressive; CrI, credible interval; e-LI, Statistics Korea e-Local Indicators; HDL-C, high-density lipoprotein cholesterol; HIRA, Health Insurance Review and Assessment Service; INLA, integrated nested Laplace approximation; IQR, interquartile range; KCHS, Korea Disease Control and Prevention Agency Community Health Survey; LDL-C, low-density lipoprotein cholesterol; MCST, Ministry of Culture, Sports and Tourism; MOHW, Ministry of Health and Welfare; NA, not applicable; NHIS, National Health Insurance Service; PIT, probability integral transform; RECORD, REporting of studies Conducted using Observational Routinely collected health Data; RR, rate ratio; RRP, resident registration population; SD, standard deviation; STROBE, Strengthening the Reporting of Observational Studies in Epidemiology; TC, total cholesterol; TG, triglycerides; WAIC, widely applicable information criterion; ΔWAIC, difference in WAIC from the principal model.")
ps = os.path.join(OUT, f"Supplementary_Material{SUF}.docx"); J.doc_title = "Supplementary Material"; J.save(ps)
subprocess.run([SOFFICE, "--headless", "-env:UserInstallation=file://" + tempfile.mkdtemp(prefix="lo_lipt_"), "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
# Separate STROBE checklist file (same table as Table S7)
JS = TX(cite="bracket", lines=False, sz=10); JS.cell_ls = 2.0
JS.para("<b>STROBE checklist</b>"); JS.para(f"Manuscript: {DTITLE}")
JS.para("Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) checklist with the REporting of studies Conducted using Observational Routinely collected health Data (RECORD) extension items for this ecological study. The same checklist is Supplementary Table S7.", before=6)
JS.table_fit(brit("STROBE checklist with the RECORD extension items for this ecological study of routinely collected data"), ["Item", "No.", "Where reported"], [[brit(a), b, brit(c)] for a, b, c in CK], "", fs_max=8)
foot_row(JS, "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology; RECORD, REporting of studies Conducted using Observational Routinely collected health Data. Locations refer to the manuscript and its Supplementary Material.", 8, 12)
pst = os.path.join(OUT, f"STROBE_Checklist{SUF}.docx"); JS.doc_title = "STROBE Checklist"; JS.save(pst)
subprocess.run([SOFFICE, "--headless", "-env:UserInstallation=file://" + tempfile.mkdtemp(prefix="lo_lipt_"), "--convert-to", "pdf", "--outdir", OUT, pst], check=True, capture_output=True)
print("saved", os.path.basename(pst))
