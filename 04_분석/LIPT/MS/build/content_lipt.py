# content_lipt.py — 치료 중 이상지질혈증(LIPT) 원고의 Methods·Results 문장(수치는 numbers_lipt에서만).
#  인용 = [@key] 또는 [@web:...]; 번호식. 단독 저자 → 1인칭 금지. 영국식 철자(dyslipidaemia), 결과 절 해석 금지.
#  제목 쌍점 금지, 시리즈 제목 틀 반복 금지.
from numbers_lipt import load, ROB, RS, EDU, IMS, MPA
import os, pandas as pd
N = load()
def fh(x): return f"{x:.4f}" if (f"{x:.3f}" == "1.000" and f"{x:.4f}" != "1.0000") else f"{x:.3f}"   # 1을 가까스로 배제하는 상한은 4자리
def ci(v, src=None):
    r = (src or N["main"])[v]; return f"RR {r['IRR']:.3f}; 95% CrI {r['lo']:.3f}–{fh(r['hi'])}"
def tci(t): return f"RR {t[0]:.3f}; 95% CrI {t[1]:.3f}–{fh(t[2]) if len(t) > 3 and t[3] else f'{t[2]:.3f}'}"
M = N["main"]; T1 = N["T1"]; G_ = N["gap"]["all_2011-24"]
S43 = lambda a, v: N["s43"][(a, v)]
dW = lambda a: N["s43_waic"][a] - N["waic_main"]
NCO = lambda o, v: N["nco"][(o, v)]
S46 = lambda a, v: N["s46"][(a, v)]
NC = lambda v: (N["negctl"][v]["IRR"], N["negctl"][v]["lo"], N["negctl"][v]["hi"])
SC = lambda s, v: N["sens_main"][s][v]
RSL = lambda v, r: N["region_slope"][f"{v}__{r}"]
EN = {"전라남도": "South Jeolla", "경상북도": "North Gyeongsang", "경상남도": "South Gyeongsang", "충청남도": "South Chungcheong", "전라북도": "North Jeolla",
      "강원도": "Gangwon", "부산시": "Busan", "충청북도": "North Chungcheong", "대구시": "Daegu", "경기도": "Gyeonggi", "서울시": "Seoul", "인천시": "Incheon",
      "광주시": "Gwangju", "울산시": "Ulsan", "대전시": "Daejeon", "세종시": "Sejong", "제주도": "Jeju"}
def sidos(d, n):
    l = [f"{EN.get(k, k)} ({v})" for k, v in list(d.items())[:n]]; return ", ".join(l[:-1]) + " and " + l[-1]
KH = ("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV")
TITLE = "Treated dyslipidaemia among Korean health-screening attendees is more common in more educated districts, with no clear link to lipid risk factors"
RUNNING = "Geography of treated dyslipidaemia"
assert ":" not in TITLE and "229" not in TITLE and "standardi" not in TITLE.lower()
KEYWORDS = "Dyslipidaemias; Hydroxymethylglutaryl-CoA reductase inhibitors; Health services accessibility; Educational status; Spatial analysis; Republic of Korea"
HIGHLIGHTS = ["Treated dyslipidaemia among screening attendees clustered in Korea's capital region",
              "Its map differed from the map of untreated suspected dyslipidaemia",
              "More educated districts had more treated dyslipidaemia across space–time models",
              "Obesity, smoking, drinking and walking showed no credible district-level association",
              "Specialists per population ran against expectation, possibly a denominator effect"]
assert 3 <= len(HIGHLIGHTS) <= 5 and all(len(h) <= 85 for h in HIGHLIGHTS), [len(h) for h in HIGHLIGHTS]
assert 3 <= len(KEYWORDS.split(";")) <= 7
_LK = pd.read_csv(os.path.join(RS, "S1_likelihood.csv")); _LK = _LK[_LK.set == "REF_forced_only"].set_index("family").WAIC
_FAM = pd.read_csv(os.path.join(RS, "S3_main_fit.csv")).family.iloc[0]
assert _FAM == "nbinomial" and _LK["nbinomial"] < _LK["poisson"] and abs(_LK["nbinomial"] - N["waic_forced"]) < 0.05
NHYP = N["n_hyp"]; EXP_CHANCE = 0.05 * NHYP; assert NHYP == 11
SUP = {"methods": 1, "covariates": 2, "checks": 3, "maps": 4, "windows": 5, "specs": 6, "posthoc": 7, "strobe": 8}
def sup(k): return f"Supplementary Section S{SUP[k]}"
_pc = lambda v: f"{100*N['mv'][v]['cred_frac']:.0f}%"
ALT = N["retention"]; LO = N["leaveout"]
NULLV = ["screening_uptake", "obesity_rate", "high_risk_drinking_rate", "current_smoking_rate", "walking_practice_rate", "public_sports_facilities_per_100k",
         "basic_livelihood_rate", "single_person_household_share"]
BEST = min(KH, key=lambda a: N["s43_waic"][a])
_EPP = float(pd.read_csv(os.path.join(RS, "S10_offset_sensitivity_IRR.csv")).set_index("cov").loc[MPA, "P_gt1"]); assert _EPP < 0.025
Y0, Y1 = N["pos_y"][2011], N["pos_y"][2024]

# 결과 주장 점검용 보조값
_Y = N["jg_yoy"]; _y1 = [_Y[y] for y in range(2012, 2018)]; _y2 = [_Y[y] for y in range(2019, 2025)]
assert _Y[2018] < min(_y1 + _y2) and N["jg_meas"][2018] < 0.36
_w1 = N['win_irr'][(EDU, 'W1_2011-17')]; _w2 = N['win_irr'][(EDU, 'W2_2018-24')]; _l1 = N['s41'][('E1_lag1', EDU)]; _l2 = N['s41'][('E2_lag2', EDU)]
assert _w1[3] and _w2[3] and _l1[3] and not _l2[3]
assert N["persist_null"]["perm_p"] < 0.001 and N["persist_null"]["poisson_p"] < 0.001 and N["ppc"]["pit_ks_p"] < 0.001
assert N["cases_min"] > 0 and N["E_min"] > 10 and N["mv_nvar"][3] == 200
assert N['moran_resid'] < 0 and N['moran_resid_p'] < 0.05
_ns = lambda v: tci(N["s43"][("no_spatial", v)])
_drk = N["win_irr"][("high_risk_drinking_rate", "W1_2011-17")]; assert _drk[3] and _drk[0] > 1 and not N["win_irr"][("high_risk_drinking_rate", "W2_2018-24")][3]
_wpsd = N["edu_within_perSD"]; _rb = N["rho_ts_boot"]
_mpaE = N["epop"][MPA]; assert _mpaE[3] and f"{_mpaE[2]:.3f}" == "1.000"
_pp = lambda x: "<0.001" if x < 0.001 else f"={x:.3f}"
_X = N["xf"]; _xt = lambda k, v: tci(_X[k][v])
_cr = [v for v in ("screening_uptake", "basic_livelihood_rate", "single_person_household_share") if _X["E_crude"][v][3]]; assert len(_cr) == 3
_oa = _X["add_out_of_area_care"]; _e84 = N["e084"]; _VP = N["varpart"]; _A = N["retention"]; _RB = N["rubin"]; _E = N["main"]

# 보충 자료 인용 자리(키 → 인용 문구). 저널판이 번호를 정한 사전을 넘긴다.
SUPKEYS = ("judgement", "methods", "covariates", "checks", "specs", "strobe", "persistence", "fig_observed", "spec_tables", "spec_table",
           "kh_table", "windows", "window_table", "posthoc")
ETHICS = "The institutional review board of Hongik University approved the study and waived informed consent because only published aggregate statistics were used."


def texts(ethics, S):
    """Methods·Results 문장 (제목, 문장) 목록. ethics = 윤리 문장, S = 보충 인용 사전(SUPKEYS)."""
    methods = [
("Design, outcome and population",
 f"This ecological study used the general health screening programme of the National Health Insurance Service, which draws on a national database covering the whole population [@cheolseong2017data] and is offered every 2 years to insured adults [@seong2017cohort]. The screening judgement places attendees who report a physician diagnosis of dyslipidaemia and current drug treatment in a separate category of existing disease; the annual number of attendees in this category was the outcome, here called treated dyslipidaemia. "
 "The criteria for this category were checked against the original tables of the Health Screening Implementation Standards (Ministry of Health and Welfare notices 2010-120 to 2023-292, the 17 versions in force in 2011–2024): in every version the category comprised attendees judged to have dyslipidaemia and currently taking medication, without a laboratory threshold, so the outcome is a programme judgement of existing disease based on the medical-history questionnaire rather than on measured lipids. "
 f"From 2018 the lipid panel was restricted to men aged 24 years or older and women aged 40 years or older every 4 years, and the history question changed from a tick grid to a yes/no item for each condition; the criteria for existing disease did not change, but the annual rise in the national share slowed in 2018 and the ratio of judged to self-reported treated attendees fell among people aged 45–59 years, an apparent change that was handled with year-specific expected numbers and the prespecified 2011–2017 and 2018–2024 windows ({S['judgement']}). "
 f"Two sets of tables for 2011–2024 were taken from the national statistics portal [@web:kosis2026screening]: district-by-sex tables of attendees and of judgement results by disease (DT_35007_N098 and DT_35007_N105; {N['n_districts']} districts, {N['cases_total']:,} attendances with treated dyslipidaemia among {N['exam_total']:,.0f} attendances), and national tables by sex and age group (19 years or younger, 5-year groups from 20–24 to 80–84 years, and 85 years or older; DT_35007_N099 and DT_35007_N106; {int(N['s22']['2011-2024']['cases_national']):,} among {int(N['s22']['2011-2024']['examinees_national']):,}), which gave the national shares used for standardisation. District sums were {N['dist_nat_pct'][0]:.1f}–{N['dist_nat_pct'][1]:.1f}% of the national totals in every year. Districts were harmonised to {N['n_districts']} units ({N['n_rows']:,} district-years); Sejong, published only as a province-level row (2012–2024) and not as a district row, was excluded and kept only in the neighbourhood graph ({S['methods']})."),
("Age and sex standardisation",
 "Expected numbers were obtained by indirect standardisation: the national share with treated dyslipidaemia in each sex and age group was applied to the attendees in each district and rescaled each year to the national total [@inskip1983methods]. Observed over expected numbers gives the standardised treatment ratio. "
 "Because expected numbers were rebuilt every year from that year's national sex- and age-specific shares, national changes in the level or slope of the outcome, including any change in 2018, were removed from the standardised ratios, which therefore compare each district with the nation in the same year. "
 f"With attendees, rather than residents, as the denominator, the ratio describes treatment among people who attended screening. Sex entered the analysis through standardisation; sex-specific associations were not examined because district covariates are not reported by sex, and sex is reported following the Sex and Gender Equity in Research (SAGER) guidelines [@heidari2016sex]. Expected numbers from attendees ranged from {N['estd_ecrude'][0]:.2f} to {N['estd_ecrude'][1]:.2f} times the crude expectation."),
("Covariates",
 "The spatial pattern was first described with models containing forced controls only. Eleven district characteristics and their expected directions were then fixed before any covariate model was fitted, in 3 groups. "
 "Care reach and selection: internal-medicine specialists per 100,000 population (expected positive), health-screening uptake (negative) and the share of adults with tertiary education (positive). "
 "Lifestyle-related risk factors: obesity, high-risk drinking and current smoking (positive), and walking, moderate-to-vigorous physical activity and public sports facilities per 100,000 (negative); behavioural rates came from the Community Health Survey [@kang2015korea]. "
 "Deprivation and household: basic livelihood security receipt and single-person households (negative). "
 "Expected directions were informed by evidence that screening participation is selective and attendees differ from non-attendees [@park2021association], that education is associated with lipid testing [@marcus2021unmet], that exercise training modestly improves blood lipids [@kodama2007effect; @smart2025effect] and that poorer people are less adherent to statins [@wallachkildemoes2013adherence], and by the assumption that living alone may reduce support for care. "
 "Five controls were forced into every model: urban population share, physicians per 1,000, sex ratio, fiscal autonomy and the share aged 80 years or older. Population density was not included because it is a marker of urbanicity, which the forced urban population share already represents, rather than a separate pathway to treated dyslipidaemia. "
 f"Internal-medicine specialist density was transformed to log(1 + specialists per 100,000), and covariates were standardised to 1 standard deviation (SD); missing years were filled by within-district interpolation, or by district or year means where a district had no observations; basic livelihood security rates were recomputed from official recipient counts of the Ministry of Health and Welfare, which replaced the source-table values, including values that had collapsed or been inflated in 2021–2023 for cities divided into general districts ({S['covariates']}; checks in {S['checks']})."),
("Statistical analysis",
 f"The likelihood (Poisson or negative binomial) was chosen by the lower widely applicable information criterion (WAIC) of the forced-controls model; zero-inflated models were not considered because the smallest expected number in any district-year was {N['E_min']:.1f} and no district-year had a zero count. "
 f"Models had an offset of log expected numbers, a Besag–York–Mollié 2 (BYM2) district effect with penalised-complexity priors [@riebler2016intuitive; @simpson2017penalising] and random-walk and independent year effects, fitted by integrated nested Laplace approximation [@rue2009approximate] in R version 4.6.0 (R Foundation for Statistical Computing, Vienna, Austria) [@web:rcore2026] with the R-INLA package; the full software list and model specification are given in {S['methods']}. "
 "The principal model had no space–time interaction, so that covariate associations were estimated from variation both between districts and within districts over time. "
 "Models without a district effect and with an intrinsic conditional autoregressive district effect only were also fitted to show how spatial structure affected the estimates. "
 f"No variance inflation factor in the principal model was 10 or more (maximum {N['vif_max']:.2f}). "
 "Rate ratios (RRs) per 1 SD are reported with 95% credible intervals (CrIs); an association was credible when the interval excluded 1. RRs are mutually adjusted ecological associations, not causal effects [@morgenstern1995ecologic]. "
 f"The analysis was exploratory and intervals were not adjusted for multiplicity; with {NHYP} hypothesis covariates, about {EXP_CHANCE:.2f} intervals excluding 1 would be expected by chance if all associations were null. "
 f"Sensitivity to covariate selection was assessed with {N['mv_nvar'][3]} random subsets of the {NHYP} hypothesis covariates, in which each covariate was included with probability 0.5 ({N['mv_nvar'][0]}–{N['mv_nvar'][2]} covariates per subset, median {N['mv_nvar'][1]:.0f}) and the 5 forced controls were always kept [@steegen2016increasing]; a covariate was subset-stable if credible in at least 75% of the subsets containing it, with the same sign in at least 95%, and an association was described as consistent when it also remained credible in the space–time interaction models and in both calendar windows. "
 "Covariate-adjusted residual hot and cold spots were districts in which the posterior probability that the residual spatial RR exceeded 1 was above 0.95 or below 0.05, for the whole period and 2 windows (2011–2017, 2018–2024) that do not cross the 2018 change in the lipid-testing schedule."),
("Sensitivity, prespecified secondary and post hoc analyses",
 "Knorr-Held type I–IV space–time interactions were added [@knorrheld2000bayesian]; subset-stable covariates were split into district means and two-way-centred within-district deviations [@bell2015explaining]; the model was refitted in each window, and interactions of each covariate with the window and with the period from 2020 onwards (the COVID-19 period) were estimated; and expected numbers were recomputed from the resident population. "
 f"Further specifications varied the likelihood, time effects, priors, neighbourhoods, age bands, forced controls, spatial confounding adjustment [@dupont2022spatial], lags, left-out provinces or years and region-specific slopes, and filled values were perturbed 20 times and the estimates pooled ({S['specs']}). "
 "District numbers of people treated for gastric cancer and for infectious disease, modelled in the same way, served as comparison outcomes, and district rates of hit-and-run accidents, fires and household waste recycling, added one at a time, as negative-control exposures [@lipsitch2010negative]; E-values quantified the confounding needed to explain associations [@vanderweele2017sensitivity]. A comparison outcome or negative-control exposure with an estimate of similar size and direction to that for treated dyslipidaemia, whether or not its interval excluded 1, was to be read as showing that the association was not specific to treated dyslipidaemia. "
 "Persistence was described with emerging hot spot analysis (Getis–Ord Gi* statistics with Mann–Kendall trend tests on empirical Bayes-smoothed annual ratios) and with Kendall's W of annual district rankings of observed ratios, compared with permutation and Poisson null distributions that keep each district's expected numbers. "
 "A secondary analysis fixed in advance compared each district's treatment ratio with its standardised ratio of suspected dyslipidaemia, the screening judgement of suspected disease given to attendees whose lipid tests were abnormal without treatment, using Spearman correlation with a district bootstrap interval and the spatial autocorrelation of the log ratio between them. "
 "The thresholds for suspected dyslipidaemia were lower in 2014–2015 (total cholesterol ≥230 mg/dL and low-density lipoprotein cholesterol ≥150 mg/dL, otherwise ≥240 and ≥160 mg/dL), and from 2018 only about one-third of attendees had a lipid panel, so suspected ratios were standardised within each window. "
 "After the results were seen, an association against the expected direction was examined post hoc with a single-covariate model; removal of physician density, tertiary education, or physician density and urban share; one-way district-mean and within-district parts; addition of unmet medical need and the shares of attendees treated for hypertension or diabetes; and specialist density per area. "
 "Further post hoc analyses were crude expected numbers (attendees multiplied by the national crude share), expected numbers from fixed 2015 national shares or with the shares at ages 75 years or older changed by 10%, exclusion of districts whose territory changed, addition of the share of patients treated outside their district of residence or of clinic or care-institution density, refits without filled cells or without 2020–2021, alternative priors for the BYM2 mixing parameter, a screening-based obesity proxy and a restricted spatial regression. Region-specific slopes were compared with the lower-WAIC of 2 baselines (common slopes, and common slopes with region main effects): a ΔWAIC of −6 or less was read as support for regional heterogeneity, −6 to −4 as weak support, −4 to 4 as no difference and more than 4 as favouring common slopes; these thresholds were set after the principal results were known."),
("Ethics statement and reporting",
 ethics + f" Reporting follows the Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement [@vonelm2007strengthening] ({S['strobe']})."),
]
    results = [
("Treated dyslipidaemia among attendees",
 f"Over 2011–2024, {N['exam_total']/1e6:.1f} million screening attendances included {N['cases_total']:,} attendances with treated dyslipidaemia (Table 1); people screened in several years contribute more than once. The crude share rose from {Y0:.1f}% in 2011 to {Y1:.1f}% in 2024, without a fall at the 2018 change in the testing schedule, although the annual increase slowed in that year ({_Y[2018]:.1f}%, against {min(_y1):.1f}–{max(_y1):.1f}% in 2012–2017 and {min(_y2):.1f}–{max(_y2):.1f}% in 2019–2024)."),
("Spatial pattern",
 f"Moran's I of observed log ratios was {N['moran_pooled']:.2f} pooled over years and ranged from {N['moran_year_min']:.2f} to {N['moran_year_max']:.2f} annually, without a monotonic trend over 2011–2024 (Kendall's τ {N['moran_year_tau'][0]:.2f}); the BYM2 spatial fraction was {N['phi'][0]:.2f} (95% CrI {N['phi'][1]:.2f}–{N['phi'][2]:.2f}). "
 f"Residual RRs ranged from {N['rr_min']:.2f} to {N['rr_max']:.2f}, with {N['n_hot']} covariate-adjusted residual hot spots, mainly in {sidos(N['hot_by_sido'], 4)}, and {N['n_cold']} cold spots, mainly in {sidos(N['cold_by_sido'], 4)} (Fig. 1A); {N['n_hot_rr110']} of the hot spots had a residual RR of 1.10 or more and {N['n_cold_rr090']} of the cold spots 0.90 or less. "
 f"The capital region held {N['hot_capital']} hot spots and {N['cold_capital']} cold spot. Residual RRs correlated with unadjusted empirical Bayes-smoothed ratios (Spearman's ρ {N['rho_resid_eb']:.2f}). "
 f"In both windows, {N['hot_all_windows']} districts were hot spots and {N['cold_all_windows']} cold spots, and annual district rankings of observed ratios were stable (Kendall's W {N['kendall_W']:.2f}; permutation and Poisson null <i>p</i><0.001) ({S['persistence']}). "
 f"Observed standardised ratios for 2011–2024 ranged from {_e84[0]:.2f} to {_e84[1]:.2f} (median {_e84[2]:.2f}) and correlated with the fitted ratios at r {_e84[3]:.2f} ({S['fig_observed']}). "
 f"The structured spatial effect had a {100*_VP['spatial_structured']['share_of_linear_predictor_var']:.1f}% share of the variance of the linear predictor, and all covariates, including forced controls, a {100*_VP['fixed_covariates']['share_of_linear_predictor_var']:.1f}% share."),
("District correlates",
 f"The negative binomial likelihood was selected (WAIC {_LK['nbinomial']:,.1f} vs {_LK['poisson']:,.1f}). "
 f"Adding the {NHYP} covariates did not improve WAIC beyond refit variability (difference {N['waic_forced_dr1']:.1f} relative to forced controls only, pointwise standard error {N['waic_forced_se']:.1f}; repeated fits of the same specification differed by up to {N['waic_refit_max']:.0f} WAIC units), so covariate sets were not ranked by WAIC. "
 f"Tertiary education, moderate-to-vigorous activity and internal-medicine specialist density were credible and subset-stable (Table 2). Treated dyslipidaemia was higher with more tertiary education ({ci(EDU)}) and lower with more moderate-to-vigorous activity ({ci(MPA)}). "
 f"It was lower with more internal-medicine specialists per population, opposite to the expected direction ({ci(IMS)}). " + ("Each was credible in all covariate subsets containing it. " if all(N["mv"][v]["cred_frac"] == 1 for v in (EDU, MPA, IMS)) else f"They were credible in {_pc(EDU)}, {_pc(MPA)} and {_pc(IMS)} of the covariate subsets containing them, respectively. ") +
 f"Obesity ({ci('obesity_rate')}), walking ({ci('walking_practice_rate')}), smoking, drinking, sports facilities, screening uptake, basic livelihood receipt and single-person households were not credibly associated (Table 2). "
 f"Without a district effect, the RRs were further from 1 (tertiary education {_ns(EDU)}; specialist density {_ns(IMS)}; activity {_ns(MPA)}) and residual Moran's I was {N['resid_moran_spec']['no_spatial']['resid_moran_I']:.2f}, and with an intrinsic conditional autoregressive district effect only, the RR for tertiary education was {N['s43'][('icar_besag', EDU)][0]:.3f} (95% CrI {N['s43'][('icar_besag', EDU)][1]:.3f}–{N['s43'][('icar_besag', EDU)][2]:.3f}) ({S['spec_tables']}). "
 f"Of the negative-control exposures, fires were credibly associated ({tci(NC('fires_per_10000'))}), and the association persisted after adding road paving ({_xt('nco_fires_per_10000_plus_road', 'fires_per_10000')}) or modelling the urban share non-linearly ({_xt('nco_fires_per_10000_urban_rw2', 'fires_per_10000')})."),
("Space–time models and sensitivity analyses",
 f"Knorr-Held type II–IV interactions fitted better than the principal model (difference in WAIC from the principal model, ΔWAIC, {dW('KH_typeIII'):,.0f} to {dW('KH_typeII'):,.0f}, type II best); type I, an observation-level effect, was not compared by WAIC. "
 f"Tertiary education remained credible in all 4 types, in both windows (2011–2017 {tci(_w1)}; 2018–2024 {tci(_w2)}), with resident-based expected numbers and with 1-year lagged covariates ({tci(_l1)}); with 2-year lagged covariates the estimate remained positive but imprecise ({tci(_l2)}; {S['spec_table']}) (Fig. 2; {S['windows']}). "
 f"In the planned decomposition, education was positively associated between districts ({tci(N['bw'][EDU + '__between'])}) and inversely within districts over time ({tci(N['bw'][EDU + '__within'])}); within-district variation was {N['edu_within_sd']:.2f} of the overall SD, so the within-district RR per 1 SD of within-district variation was {_wpsd[0]:.3f} (95% CrI {_wpsd[1]:.3f}–{_wpsd[2]:.3f}). "
 "Moderate-to-vigorous activity was not credible in types II–IV or in either window, and specialist density was not credible in types II and IV or in either window. "
 f"Of the other covariates, physician density, a forced control, became credible in type IV ({tci(S43('KH_typeIV', 'physicians_per_1000'))}) and single-person households in type I ({tci(S43('KH_typeI', 'single_person_household_share'))}); all changes in credibility are listed in {S['kh_table']}. "
 f"High-risk drinking was positively associated in 2011–2017 only ({tci(_drk)}) and walking, against the expected direction, in 2018–2024 only ({tci(N['win_irr'][('walking_practice_rate', 'W2_2018-24')])}); {N['n_win_int']} of the {NHYP} covariates had credible interactions with calendar window and {N['covid_nint']} with the period from 2020 onwards ({S['window_table']}). "
 f"Across {_A[EDU]['n_specs']} alternative specifications, tertiary education was credible in {_A[EDU]['kept']}, specialist density in {_A[IMS]['kept']} and activity in {_A[MPA]['kept']}. "
 f"With filled values perturbed 20 times, these 3 covariates were credible in {_RB[EDU]['n_cred']}, {_RB[IMS]['n_cred']} and {_RB[MPA]['n_cred']} of 20 fits, with pooled RRs of {_RB[EDU]['IRR_pooled']:.3f}, {_RB[IMS]['IRR_pooled']:.3f} and {_RB[MPA]['IRR_pooled']:.3f} against {_E[EDU]['IRR']:.3f}, {_E[IMS]['IRR']:.3f} and {_E[MPA]['IRR']:.3f} in the principal model. "
 f"Tertiary education stayed credible when each province ({LO[('province', EDU)][1]} of {LO[('province', EDU)][0]}) or year ({LO[('year', EDU)][1]} of {LO[('year', EDU)][0]}) was left out. E-values were {N['evalue'][EDU]['E_point']:.2f} for education, {N['evalue'][IMS]['E_point']:.2f} for specialists and {N['evalue'][MPA]['E_point']:.2f} for activity, and, against the better-fitting of 2 baselines (common slopes), region-specific slopes lowered WAIC for specialist density (ΔWAIC {N['region_dwaic'][IMS]:.1f}) but not for moderate-to-vigorous activity ({N['region_dwaic'][MPA]:+.1f}); for tertiary education the region-specific model fitted much worse ({N['region_dwaic'][EDU]:+.1f}) and was unstable, so regional differences in the education association could not be estimated ({S['specs']}). "
 f"With expected numbers from residents, education remained credible ({tci(N['epop'][EDU])}), activity was credible at the margin (RR {_mpaE[0]:.3f}; 95% CrI {_mpaE[1]:.3f}–{_mpaE[2]:.3f}, upper bound below 1 before rounding; posterior probability of RR above 1, {_EPP:.3f}), and specialist density was not credibly associated ({tci(N['epop'][IMS])}). "
 f"With crude expected numbers, in which sex and age entered only through the forced sex ratio and share aged 80 years or older, tertiary education was not credibly associated ({_xt('E_crude', EDU)}), whereas screening uptake ({_xt('E_crude', 'screening_uptake')}), basic livelihood receipt ({_xt('E_crude', 'basic_livelihood_rate')}) and single-person households ({_xt('E_crude', 'single_person_household_share')}) were; with expected numbers from fixed 2015 national shares, education remained credible ({_xt('E_fix2015', EDU)}). "
 f"Excluding the 3 districts whose territory or province changed during 2011–2024, education ({_xt('D145_drop_boundary3', EDU)}) and moderate-to-vigorous activity ({_xt('D145_drop_boundary3', MPA)}) remained credible, whereas specialist density did not ({_xt('D145_drop_boundary3', IMS)}). "
 f"In the comparison outcomes, education had an RR of {N['nco'][('INFECT', EDU)][0]:.3f} for infectious disease (95% CrI {N['nco'][('INFECT', EDU)][1]:.3f}–{N['nco'][('INFECT', EDU)][2]:.3f}) and {N['nco'][('GCA', EDU)][0]:.3f} for gastric cancer (95% CrI {N['nco'][('GCA', EDU)][1]:.3f}–{N['nco'][('GCA', EDU)][2]:.3f}), and specialist density {N['nco'][('INFECT', IMS)][0]:.3f} (95% CrI {N['nco'][('INFECT', IMS)][1]:.3f}–{N['nco'][('INFECT', IMS)][2]:.3f}) and {N['nco'][('GCA', IMS)][0]:.3f} (95% CrI {N['nco'][('GCA', IMS)][1]:.3f}–{N['nco'][('GCA', IMS)][2]:.3f}); these coefficients were not formally compared with those for treated dyslipidaemia. "
 f"Residual Moran's I was {N['moran_resid']:.2f} (two-sided permutation <i>p</i>≈{N['moran_resid_p']:.3f}; {N['moran_perm']} permutations, seed {N['moran_resid_seed']}); 95% predictive intervals covered {100*N['oos']['coverage95']:.1f}% of 2024 numbers held out with covariates known, and the probability integral transform departed from uniformity (Kolmogorov–Smirnov <i>p</i><0.001)."),
("Post hoc analyses of specialist density",
 f"The inverse association of specialist density persisted alone ({tci(S46('P2_alone', IMS))}) and without physician density and urban share ({tci(S46('P3c_drop_physicians_urban', IMS))}). In a one-way split it lay in district means ({S['spec_table']}; {tci(S46('P4_between_within', IMS + '__B'))}) and not in within-district changes ({tci(S46('P4_between_within', IMS + '__W'))}), whereas neither part was credible in the planned two-way decomposition ({tci(N['bw'][IMS + '__between'])} between), and it was confined to the capital region ({tci(RSL(IMS, 'Capital'))}) and Chungcheong ({tci(RSL(IMS, 'Chungcheong'))}). "
 f"Specialist density per area, computed from specialist counts, was not credibly associated, alone ({tci(S46('P5_per_area', 'spec_per_km2_log'))}) or together with density per population ({tci(S46('P5b_both', 'spec_per_km2_log'))}), while density per population stayed inverse in that model ({tci(S46('P5b_both', IMS))}) ({S['posthoc']}). "
 f"When the share of patients treated outside their district of residence was added, specialist density was no longer credibly associated ({tci(_oa[IMS])}), whereas the out-of-district share was inversely associated ({tci(_oa['out_of_area_care_share'])}); clinic density ({_xt('add_clinics_per_100k', 'clinics_per_100k')}) and care-institution density ({_xt('add_care_institutions_per_100k', 'care_institutions_per_100k')}) were not credibly associated ({S['spec_table']})."),
("Treated versus suspected dyslipidaemia",
 f"District treatment ratios were weakly and inversely correlated with ratios of suspected dyslipidaemia (Spearman's ρ {_rb[0]:.2f}; 95% bootstrap interval {_rb[1]:.2f} to {_rb[2]:.2f}). Of {G_['n']} districts, {G_['quadrants']['treated high / suspected low']} had a treatment ratio above 1 with a suspected ratio of 1 or less, mostly in Seoul and Gyeonggi, and {G_['quadrants']['treated low / suspected high']} the reverse, mostly in the Jeolla provinces, Busan and the Gyeongsang and Chungcheong provinces (Fig. 1B). The log ratio between treated and suspected dyslipidaemia was spatially clustered (Moran's I {G_['moran_G']:.2f}) and correlated with tertiary education (ρ {G_['rho_G_tertiary']:.2f}) and inversely with specialist density (ρ {G_['rho_G_im']:.2f})."),
]
    import re as _re2
    _mn = lambda t: _re2.sub(r"(^|[\s(;,])-(?=\d)", "\\1\u2212", t)   # 음수는 진짜 마이너스(U+2212)
    return [(h, _mn(t)) for h, t in methods], [(h, _mn(t)) for h, t in results]


# 기본판(보충 번호 없음). 저널판은 texts(ETHICS, SUPMAP)으로 다시 만든다.
METHODS, RESULTS = texts(ETHICS, {k: "the Supplementary Material" for k in SUPKEYS})

# 문장 주장 대조(결과표와 어긋나면 빌드 중단)
assert N["n_cred_hyp"] == 3 and N["n_robust"] == 3 and N["waic_main"] > N["waic_forced"] and BEST == "KH_typeII"
assert all(M[v]["cred"] for v in ROB) and M[EDU]["IRR"] > 1 and M[IMS]["IRR"] < 1 and M[MPA]["IRR"] < 1
assert not any(M[v]["cred"] for v in NULLV) and N["negctl"]["fires_per_10000"]["cred"] and not N["negctl"]["hit_and_run_rate"]["cred"] and not N["negctl"]["waste_recycling_rate"]["cred"]
assert all(dW(a) < 0 for a in KH) and all(S43(a, EDU)[3] for a in KH) and not any(S43(a, MPA)[3] for a in ("KH_typeII", "KH_typeIII", "KH_typeIV"))
assert not S43("KH_typeII", IMS)[3] and not S43("KH_typeIV", IMS)[3]
assert all(N["win_irr"][(EDU, w)][3] for w in ("W1_2011-17", "W2_2018-24")) and not any(N["win_irr"][(v, w)][3] for v in (IMS, MPA) for w in ("W1_2011-17", "W2_2018-24"))
assert N['win_irr'][('walking_practice_rate', 'W2_2018-24')][3] and N['win_irr'][('walking_practice_rate', 'W2_2018-24')][0] > 1 and not N['win_irr'][('walking_practice_rate', 'W1_2011-17')][3]
assert N["epop"][EDU][3] and N["epop"][MPA][3] and not N["epop"][IMS][3]
assert S46("P2_alone", IMS)[3] and S46("P3c_drop_physicians_urban", IMS)[3] and S46("P4_between_within", IMS + "__B")[3] and not S46("P4_between_within", IMS + "__W")[3]
assert not S46("P5_per_area", "spec_per_km2_log")[3] and not S46("P5b_both", "spec_per_km2_log")[3] and S46("P5b_both", IMS)[3]   # 면적당 전문의 밀도는 단독·동시 투입 모두 비credible
assert S43("KH_typeIV", "physicians_per_1000")[3] and not M["physicians_per_1000"]["cred"] and S43("KH_typeI", "single_person_household_share")[3] and not M["single_person_household_share"]["cred"]
assert N["region_dwaic"][IMS] <= -6 and N["region_dwaic"][MPA] > -4 and N["region_dwaic"][EDU] > 4
assert RSL(IMS, "Capital")[3] and RSL(IMS, "Chungcheong")[3] and not any(RSL(IMS, r)[3] for r in ("Yeongnam", "Honam", "Gangwon_Jeju"))
assert LO[("province", EDU)] == (16, 15) and LO[("year", EDU)] == (14, 14) and N["rubin"][EDU]["n_cred"] == 20   # 시도 하나씩 제외 15/16
assert G_["rho_lipt_susp"] < 0 and G_["moran_G_p"] <= 0.001 and list(N["hot_by_sido"])[:2] == ["서울시", "경기도"] and abs(Y1 - 12.6) < 0.1

if __name__ == "__main__":
    import re
    for h, t in METHODS + RESULTS: print("##", h, "\n", t, "\n")
    print("words M", sum(len(re.sub(r"\[@[^\]]+\]", "", t).split()) for _, t in METHODS), "R", sum(len(re.sub(r"\[@[^\]]+\]", "", t).split()) for _, t in RESULTS))
