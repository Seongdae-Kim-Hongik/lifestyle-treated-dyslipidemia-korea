# content_manuscript_lipt.py — Angiology(Sage, 단일 익명) 원고 설정: 문장은 content_lipt.texts()에서 만들고 제목·running title·키워드·윤리 문장·보충 번호·끝 절 진술만 정한다.

from content_lipt import *
import content_lipt as _B
import re as _re
_LK = _B._LK
TITLE = "Do lifestyle risk factors explain where Koreans report treated dyslipidemia?"
RUNNING = "Lifestyle and treated dyslipidemia"
assert ":" not in TITLE and "229" not in TITLE and "standardi" not in TITLE.lower() and len(RUNNING) <= 40
KEYWORDS = "Dyslipidemias; Life style; Educational status; Spatial analysis; Republic of Korea"
assert 4 <= len(KEYWORDS.split(";")) <= 5
# Methods 윤리 문장은 한 문장(세부는 Statements and Declarations).
ETHICS = ("The Institutional Review Board of Hongik University approved the study and waived informed consent; approval numbers and dates are given under Statements and Declarations.")
# 보충 자료 인용 문구(본문 첫 인용 순, build_supplement_lipt.py 섹션·표·그림 순서와 짝).
SUPMAP = {"judgement": "Supplementary Section S1 and Supplementary Tables S1 and S2",
          "methods": "Supplementary Section S1",
          "covariates": "Supplementary Section S2 and Supplementary Table S3",
          "checks": "Supplementary Section S3 and Supplementary Table S4",
          "specs": "Supplementary Section S4 and Supplementary Tables S5 and S6",
          "strobe": "Supplementary Section S5 and Supplementary Table S7",
          "persistence": "Supplementary Section S6, Supplementary Table S8 and Supplementary Fig. S1",
          "fig_observed": "Supplementary Fig. S2",
          "spec_tables": "Supplementary Tables S5 and S6",
          "spec_table": "Supplementary Table S5",
          "kh_table": "Supplementary Table S6",
          "windows": "Supplementary Section S7 and Supplementary Table S9",
          "window_table": "Supplementary Table S9",
          "posthoc": "Supplementary Section S8 and Supplementary Table S10"}
assert set(SUPMAP) == set(_B.SUPKEYS)
METHODS, RESULTS = _B.texts(ETHICS, SUPMAP)
_txt = " ".join(t for _, t in METHODS + RESULTS)
assert list(dict.fromkeys(_re.findall(r"Supplementary Section S(\d)", _txt))) == [str(i) for i in range(1, 9)]
_tabs = list(dict.fromkeys(int(x) for g in _re.findall(r"Supplementary Tables? S(\d+)(?: and S(\d+))?", _txt) for x in g if x))
assert _tabs == list(range(1, 11)), _tabs
assert _txt.find("Supplementary Fig. S1") < _txt.find("Supplementary Fig. S2")
assert "first submission" not in _txt
# 끝 절(Acknowledgements → Author Contributions → Statements and Declarations)
AI_STATEMENT = ("During the preparation of this work, the author used Claude Opus 5.5 (Anthropic) and ChatGPT (GPT-6 Astra; OpenAI) only for translation and English-language editing of the manuscript. "
                "The author reviewed and edited all output and takes full responsibility for the content of the manuscript.")
CONTRIB = ("Seongdae Kim: conceptualization, data curation, formal analysis, investigation, methodology, software, validation, visualization, "
           "writing (original draft) and writing (review and editing).")
IRB1 = ("7002340-202511-HR-012", "4 November 2025"); IRB2 = ("7002340-202611-HR-040", "3 November 2026")
REPO_PH = "https://github.com/Seongdae-Kim-Hongik/lifestyle-treated-dyslipidemia-korea"; ZEN_PH = "10.5281/zenodo.24556621"   # 새 저장소·concept DOI(예약, 게시는 투고 직전)
STATEMENTS = [
    ("Ethical considerations", f"This study was approved by the Institutional Review Board of Hongik University (approval no. {IRB1[0]}, approved on {IRB1[1]}), and its continuing review was approved by the same board (approval no. {IRB2[0]}, approved on {IRB2[1]})."),
    ("Consent to participate", "The Institutional Review Board of Hongik University waived the requirement for informed consent because only published district-level aggregate statistics were used and no individual-level data were accessed."),
    ("Consent for publication", "Not applicable."),
    ("Declaration of conflicting interest", "The author declared no potential conflicts of interest with respect to the research, authorship, and/or publication of this article."),
    ("Funding statement", "The author received no financial support for the research, authorship, and/or publication of this article."),
    ("Data availability", "The source data are publicly available from the Korean Statistical Information Service (https://kosis.kr) and the other national statistics cited in the Methods. "
                          f"The analysis code that generates every number, table and figure is openly available on GitHub ({REPO_PH}) and Zenodo (https://doi.org/{ZEN_PH}) under the MIT license. "
                          "The processed district-year data are available from the author on reasonable request."),
]
assert [h for h, _ in STATEMENTS] == ["Ethical considerations", "Consent to participate", "Consent for publication", "Declaration of conflicting interest", "Funding statement", "Data availability"]
assert not _re.search(r"(?i)\bexempt", " ".join(t for _, t in STATEMENTS) + ETHICS)
OLD_TRACES = ()
