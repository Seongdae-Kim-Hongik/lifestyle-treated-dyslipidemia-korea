# content_manuscript_lipt.py: manuscript settings (single-blind). Sentences come from content_lipt.texts(); this file sets only the title, running title, keywords,
#  ethics sentence, supplementary labels and closing statements. 4-5 keywords; no colons in the title.
from content_lipt import *          # noqa: F401,F403  (N, ci, tci, sup, fh, dW, EDU, IMS, MPA ...)
import content_lipt as _B
import re as _re
_LK = _B._LK
TITLE = "Do lifestyle risk factors explain where Koreans report treated dyslipidemia?"
RUNNING = "Lifestyle and treated dyslipidemia"
assert ":" not in TITLE and "229" not in TITLE and "standardi" not in TITLE.lower() and len(RUNNING) <= 40
KEYWORDS = "Dyslipidemias; Life style; Educational status; Spatial analysis; Republic of Korea"
assert 4 <= len(KEYWORDS.split(";")) <= 5
# One-sentence ethics statement in Methods (details under Statements and Declarations).
ETHICS = ("The Institutional Review Board of Hongik University approved the study and waived informed consent; approval numbers and dates are given under Statements and Declarations.")
# Supplementary citation labels (order of first citation in the text, matching the section/table/figure order in build_supplement_lipt.py).
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
# P in upper-case italics with spaces around the operator
def PFIX(t): return _re.sub(r"<i>[pP]</i>\s*([<=≈>])\s*", lambda m: f"<i>P</i> {m.group(1)} ", t)
METHODS = [(h, PFIX(t)) for h, t in METHODS]; RESULTS = [(h, PFIX(t)) for h, t in RESULTS]
assert "<i>p</i>" not in " ".join(t for _, t in METHODS + RESULTS)
_txt = " ".join(t for _, t in METHODS + RESULTS)
assert list(dict.fromkeys(_re.findall(r"Supplementary Section S(\d)", _txt))) == [str(i) for i in range(1, 9)]
_tabs = list(dict.fromkeys(int(x) for g in _re.findall(r"Supplementary Tables? S(\d+)(?: and S(\d+))?", _txt) for x in g if x))
assert _tabs == list(range(1, 11)), _tabs
assert _txt.find("Supplementary Fig. S1") < _txt.find("Supplementary Fig. S2")
assert "first submission" not in _txt
# Closing sections (Acknowledgements -> Author Contributions -> Statements and Declarations)
AI_STATEMENT = "The author used Claude Opus 5.5 (Anthropic) and ChatGPT (GPT-6 Astra; OpenAI) only for translation and English-language editing of the manuscript."   # One-sentence statements only
CONTRIB = ("Seongdae Kim: conceptualization, data curation, formal analysis, investigation, methodology, software, validation, visualization, "
           "writing (original draft) and writing (review and editing).")
IRB1 = ("7002340-202511-HR-012", "4 November 2025"); IRB2 = ("7002340-202611-HR-040", "3 November 2026")
REPO_PH = "https://github.com/Seongdae-Kim-Hongik/lifestyle-treated-dyslipidemia-korea"; ZEN_PH = "10.5281/zenodo.24560215"   # Code repository and concept DOI
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
