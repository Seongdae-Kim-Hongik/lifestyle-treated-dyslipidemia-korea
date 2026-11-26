
TFIX = {"rhee2019guidelines": "2018 guidelines for the management of dyslipidemia in Korea","kang2015korea": "Korea Community Health Survey data profiles",
        "heidari2016sex": "Sex and gender equity in research: rationale for the SAGER guidelines and recommended use",
        "kwon2025dyslipidemia": "Dyslipidemia fact sheet in South Korea, 2024",
        "kwon2026cardiovascular": "Cardiovascular disease incidence and lipid-lowering medication use in Korean adults with dyslipidemia: a nationwide population-based retrospective cohort study from 2010 to 2019",
        "ray2022world": "World Heart Federation cholesterol roadmap 2022",
        "simpson2017penalising": "Penalising model component complexity: a principled, practical approach to constructing priors",
        "smart2025effect": "The effect of exercise training on blood lipids: a systematic review and meta-analysis",
        "zheutlin2024association": "Association between pharmacy proximity with cardiovascular medication use and risk factor control in the United States",
        "stocks2009gender": "Gender, socioeconomic status, need or access? Differences in statin prescribing across urban, rural and remote Australia",
        "mach2019esc": "2019 ESC/EAS guidelines for the management of dyslipidaemias: lipid modification to reduce cardiovascular risk",
        "ncdrisc2020repositioning": "Repositioning of the global epicentre of non-optimal cholesterol",
        "ctt2010efficacy": "Efficacy and safety of more intensive lowering of LDL cholesterol: a meta-analysis of data from 170,000 participants in 26 randomised trials",
        "lee2025national": "National trends in dyslipidemia prevalence, awareness, treatment, and control in South Korea from 2005 to 2022",
        "lee2025inter": "Inter-regional patient outmigration to Seoul in South Korea: the role of regional healthcare quality perceptions",
        "han2021regional": "Regional and income disparities in treatment and drug adherence of patients with dyslipidemia: a retrospective cohort study in South Korea, 2003-2015",
        "marcus2021unmet": "Unmet need for hypercholesterolemia care in 35 low- and middle-income countries: a cross-sectional study of nationally representative surveys",
        "hartz2006why": "Why do sales of lipid-lowering drugs vary between counties in Norway? Evidence from the OPPHED Health Study 2000-2001",
        "ashworth2007social": "Social deprivation and statin prescribing: a cross-sectional analysis using data from the new UK general practitioner 'Quality and Outcomes Framework'",
        "erickson2014geospatial": "Geospatial analysis of statin adherence using pharmacy claims data in the state of Michigan",
        "kodama2007effect": "Effect of aerobic exercise training on serum levels of high-density lipoprotein cholesterol: a meta-analysis",
        "wallachkildemoes2013adherence": "Adherence to preventive statin therapy according to socioeconomic position",
        "cheolseong2017data": "Data resource profile: the National Health Information Database of the National Health Insurance Service in South Korea",
        "riebler2016intuitive": "An intuitive Bayesian spatial model for disease mapping that accounts for scaling",
        "lipsitch2010negative": "Negative controls: a tool for detecting confounding and bias in observational studies"}

TAB1_COV = [("pop80_share", "Population aged 80 years or older, %"), ("tertiary_educated_share", "Tertiary education, % of adults"),
            ("im_specialists_per_100k", "Internal-medicine specialists per 100,000"), ("screening_uptake", "Health-screening uptake, %"),
            ("obesity_rate", "Obesity, %"), ("walking_practice_rate", "Walking practice, %"), ("moderate_pa_rate", "Moderate-to-vigorous activity, %"),
            ("public_sports_facilities_per_100k", "Public sports facilities per 100,000")]

GROUPS = [("Care reach and selection", ["im_specialists_per_100k", "screening_uptake", "tertiary_educated_share"]),
          ("Lipid risk factors", ["obesity_rate", "high_risk_drinking_rate", "current_smoking_rate", "walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]),
          ("Deprivation and household", ["basic_livelihood_rate", "single_person_household_share"]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {"im_specialists_per_100k": "Internal-medicine specialists", "screening_uptake": "Health-screening uptake", "tertiary_educated_share": "Tertiary education",
         "obesity_rate": "Obesity", "high_risk_drinking_rate": "High-risk drinking", "current_smoking_rate": "Current smoking", "walking_practice_rate": "Walking practice",
         "moderate_pa_rate": "Moderate-to-vigorous activity", "public_sports_facilities_per_100k": "Public sports facilities", "basic_livelihood_rate": "Basic livelihood security",
         "single_person_household_share": "Single-person households", "urban_population_share": "Urban population share", "physicians_per_1000": "Physicians per 1,000",
         "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Aged 80 years or older"}

FIGCAP = {
 1: ("Geography of treated dyslipidaemia and its relation to suspected dyslipidaemia among health-screening attendees, Korea, 2011–2024.",
     "(A) Residual spatial rate ratio (RR) by district, the posterior mean of the exponentiated Besag–York–Mollié 2 district effect from the principal model, in 6 fixed classes. Solid outlines, covariate-adjusted residual hot spots (posterior probability that the residual spatial RR exceeded 1 above 0.95); dashed outlines, cold spots (below 0.05); thick lines, province boundaries. (B) Districts classified by whether the sex- and age-standardised ratios of treated dyslipidaemia and of suspected untreated dyslipidaemia (the screening judgement of suspected disease) for 2011–2024 exceeded 1. In both panels, numbers in parentheses are districts; no data, Sejong, published only as a province-level row and excluded; the bar shows 0, 50 and 100 km and the triangle points north. District boundaries as of 2024."),
 2: ("Rate ratios for the 3 subset-stable district characteristics in the space–time, calendar-window and resident-denominator models.",
     "Symbols show rate ratios per 1 standard deviation (SD) and lines their 95% credible intervals (CrIs) from models with Knorr-Held type II (best fitting) and type IV space–time interactions, the principal model fitted to 2011–2017 and to 2018–2024 only, and the principal model with expected numbers computed from residents instead of attendees; the numbers on the right repeat each estimate. Filled symbols, CrI excludes 1; open symbols, CrI includes 1; intervals with a bound shown as 1.000 were classified from unrounded values. The shaded band and the vertical line within it mark the principal-model CrI and estimate, which are given in Table 2. The dotted vertical line marks a rate ratio of 1."),
}


SRCEN = {
 "urban_population_share": ("Statistics Korea e-Local Indicators, urban-zone population", "2011–2024"),
 "physicians_per_1000": ("Statistics Korea e-Local Indicators, physicians in medical institutions", "2011–2024"),
 "sex_ratio": ("Statistics Korea e-Local Indicators, resident registration", "2011–2024"),
 "fiscal_independence": ("Statistics Korea e-Local Indicators, local finance", "2011–2024"),
 "pop80_share": ("Resident registration population by 5-year age group", "2011–2024"),
 "im_specialists_per_100k": ("Health Insurance Review and Assessment Service, specialists by district", "2011–2024"),
 "screening_uptake": ("National Health Insurance Service, health screening statistics", "2011–2024"),
 "tertiary_educated_share": ("Statistics Korea Population and Housing Census†", "2010, 2015, 2020"),
 "obesity_rate": ("Korea Disease Control and Prevention Agency Community Health Survey‡", "2011–2024 except 2019"),
 "high_risk_drinking_rate": ("Community Health Survey‡", "2011–2024"),
 "current_smoking_rate": ("Community Health Survey‡", "2011–2024"),
 "walking_practice_rate": ("Community Health Survey‡", "2011–2024"),
 "moderate_pa_rate": ("Community Health Survey‡", "2011–2024 except 2018"),
 "public_sports_facilities_per_100k": ("Ministry of Culture, Sports and Tourism, national public sports facilities", "2011–2024"),
 "basic_livelihood_rate": ("Ministry of Health and Welfare, basic livelihood security recipients", "2011–2024"),
 "single_person_household_share": ("Statistics Korea e-Local Indicators, census-based households", "2015–2024"),
}
UNIT = {"urban_population_share": "% of residents", "physicians_per_1000": "per 1,000 residents", "sex_ratio": "men per 100 women", "fiscal_independence": "% of budget", "pop80_share": "% of residents",
        "im_specialists_per_100k": "per 100,000 residents", "screening_uptake": "% of invited people", "tertiary_educated_share": "% of adults", "obesity_rate": "% of respondents", "high_risk_drinking_rate": "% of respondents",
        "current_smoking_rate": "% of respondents", "walking_practice_rate": "% of respondents", "moderate_pa_rate": "% of respondents", "public_sports_facilities_per_100k": "per 100,000 residents",
        "basic_livelihood_rate": "% of residents", "single_person_household_share": "% of households"}
assert set(SRCEN) == set(LABEL) == set(UNIT) and len(SRCEN) == 16

# 11/26 새 인용 키 문장형 표제(고유명사만 대문자)
TFIX.update({"jin2023dyslipidemia": "Dyslipidemia fact sheet in South Korea, 2022",
 "kang2022current": "Current status of the national health screening programs in South Korea",
 "oh2026validation": "Validation of self-reported disease history in Korea: a National Health Insurance cohort study",
 "kim2017evaluation": "Evaluation of geographic indices describing health care utilization",
 "kim2018prevalence": "Prevalence of overweight and income gaps in 245 districts of Korea: comparison using the National Health Screening Database and the Community Health Survey, 2009-2014",
 "korhonen2020lifestyle": "Lifestyle changes in relation to initiation of antihypertensive and lipid-lowering medication: a cohort study",
 "park2021association": "Association of participation in health check-ups with risk factors for cardiovascular diseases",
 "yun2023socioeconomic": "Socioeconomic disparities in the association between all-cause mortality and health check-up participation among healthy middle-aged workers: a nationwide study"})

# 11/26 Table 1용 짧은 출처(약어는 표 각주에 풀이), 연도
SRCAB = {"urban_population_share": "e-LI", "physicians_per_1000": "e-LI", "sex_ratio": "e-LI", "fiscal_independence": "e-LI", "pop80_share": "RRP",
         "im_specialists_per_100k": "HIRA", "screening_uptake": "NHIS", "tertiary_educated_share": "Census†", "obesity_rate": "KCHS‡",
         "high_risk_drinking_rate": "KCHS‡", "current_smoking_rate": "KCHS‡", "walking_practice_rate": "KCHS‡", "moderate_pa_rate": "KCHS‡",
         "public_sports_facilities_per_100k": "MCST", "basic_livelihood_rate": "MOHW", "single_person_household_share": "e-LI"}
YRAB = {"tertiary_educated_share": "2010–20", "obesity_rate": "2011–24§", "moderate_pa_rate": "2011–24§", "single_person_household_share": "2015–24"}
SRC_FOOT = ("e-LI, Statistics Korea e-Local Indicators; RRP, resident registration population; HIRA, Health Insurance Review and Assessment Service; NHIS, National Health Insurance Service health screening statistics; "
            "Census, Statistics Korea Population and Housing Census; KCHS, Korea Disease Control and Prevention Agency Community Health Survey; MCST, Ministry of Culture, Sports and Tourism national public sports facilities; "
            "MOHW, Ministry of Health and Welfare basic livelihood security recipients.")
assert set(SRCAB) == set(LABEL)
