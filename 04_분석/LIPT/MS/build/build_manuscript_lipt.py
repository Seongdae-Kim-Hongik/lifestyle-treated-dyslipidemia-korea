# build_manuscript_lipt.py: assembles the manuscript and the title page (Original Article).
#  Single-blind (author details allowed). 1-inch margins, 12 pt, double spacing; header = author surname + running title, page number top right.
#  Order: title page (title, names, degrees, affiliations, correspondence, funding, presentations) -> structured abstract (<=200 words) and 4-5 keywords
#  -> Introduction -> Methods -> Results -> Discussion -> Conclusion -> Acknowledgements -> Author Contributions -> Statements and Declarations
#  -> References (Vancouver: >6 authors = first 3 + et al., NLM abbreviations, Year;Vol:pages) -> tables (one per page, three rules) -> figure legends. Figures are separate TIFFs.
#  Usage: run_all_lipt.sh
import os, re, json, subprocess, shutil, tempfile
from docx.shared import Pt, Cm
from docx.enum.text import WD_TAB_ALIGNMENT, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx_engine import JKMS
from american import amer
import content_manuscript_lipt as C
SOFFICE = os.environ.get("SOFFICE") or shutil.which("soffice") or shutil.which("libreoffice")
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.environ.get("LIPT_OUT") or os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True); SUF = os.environ.get("LIPT_SUFFIX", "")
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_lipt.json"), encoding="utf-8"))
DRAFT = os.environ.get("LIPT_DRAFT") or os.path.join(MS, "draft", "03_manuscript.md")
TITLE = C.TITLE; RUNNING = C.RUNNING; ORCID = "0000-0002-1525-0091"; PHONE = "+82-2-320-1114"; EMAIL = "kimsd@hongik.ac.kr"
AUTHOR = "Seongdae Kim, PhD"; SURNAME = "Kim"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Korea"
AI_STATEMENT = C.AI_STATEMENT; CONTRIB = C.CONTRIB; STATEMENTS = C.STATEMENTS
FUNDING = dict(STATEMENTS)["Funding statement"]; COI = dict(STATEMENTS)["Declaration of conflicting interest"]
PRESENTED = "This work has not been presented at a meeting."
SZ = 12
MSF = f"Manuscript{SUF}.docx"; TPF = f"Title_Page{SUF}.docx"

# Name provinces from the result files (hot/cold spot counts by province; top provinces in the low-treatment/high-suspicion quadrant)
_EN2 = {"전라": "the Jeolla provinces", "경상": "the Gyeongsang provinces", "충청": "the Chungcheong provinces", "부산": "Busan", "경기": "Gyeonggi", "강원": "Gangwon", "서울": "Seoul", "인천": "Incheon", "광주": "Gwangju", "대구": "Daegu", "대전": "Daejeon", "울산": "Ulsan", "제주": "Jeju"}
def _and(l): return ", ".join(l[:-1]) + " and " + l[-1]
_FAM = lambda k: {"전라남도": "전라", "전라북도": "전라", "경상남도": "경상", "경상북도": "경상", "충청남도": "충청", "충청북도": "충청"}.get(k, k[:2])
_cf = {}
for _k, _v in N["cold_by_sido"].items(): _cf[_FAM(_k)] = _cf.get(_FAM(_k), 0) + _v
_ct = [k for k, _ in sorted(_cf.items(), key=lambda x: -x[1])[:2]]
COLD_SIDO = ("the " + " and ".join(_EN2[k].split()[1] for k in _ct) + " provinces") if all(_EN2[k].endswith("provinces") for k in _ct) else _and([_EN2[k] for k in _ct])   # Top 2 province groups
_q = N["gap"]["all_2011-24"]["quadrant_by_sido"]["treated low / suspected high"]; GAP_SIDO = _and([_EN2[k] for k, _ in sorted(_q.items(), key=lambda x: -x[1])[:2]])
assert list(N["hot_by_sido"])[:2] == ["서울시", "경기도"]
def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    _e = N["main"][C.EDU]; _ph = {"N_DISTRICTS": f"{N['n_districts']}", "N_HYP": f"{N['n_hyp']}", "N_FORCED": f"{sum(1 for v in N['main'].values() if v['role'] == 'forced')}",
           "N_ATTEND_M": f"{N['T1']['2011-2024']['exam']/1e6:.1f}", "N_CASES_M": f"{N['T1']['2011-2024']['cases']/1e6:.1f}",
           "RR_EDU": f"RR {_e['IRR']:.3f}; 95% CrI {_e['lo']:.3f}–{C.fh(_e['hi'])}", "RHO_TS": f"{N['gap']['all_2011-24']['rho_lipt_susp']:.2f}",
           "VS_COV": f"{100*N['varpart']['fixed_covariates']['share_of_linear_predictor_var']:.0f}", "COLD_SIDO": COLD_SIDO, "GAP_SIDO": GAP_SIDO}
    md = re.sub(r"⟦([A-Z_]+)⟧", lambda m: _ph[m.group(1)], md); assert "⟦" not in md
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t):   # "text [@a; @b]." -> "text.{{a,b}}" (superscript after punctuation)
    f = lambda m: (m.group(2) or "") + "{{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}"
    return re.sub(r"\s*\[(@[^\]]+)\]([.,;:])?", f, t)
def all_keys():
    src = " ".join(t for _, t in C.METHODS + C.RESULTS) + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()
ABL = ("Objective", "Methods", "Results", "Conclusion")

# ── Vancouver: all authors if <=6, else first 3 + et al.; NLM journal abbreviation followed by a period; "Year;Vol:pages." without issue, month or PMID.
AUTH = {"okuyama2019effect": ["Okuyama K", "Akai K", "Kijima T", "Abe T", "Isomura M", "Nabika T"], "rhee2019guidelines": ["Rhee EJ", "Kim HC", "Kim JH", "Lee EY", "Kim BJ", "Kim EM", "Song Y", "Lim JH"], "mach2019esc": ["Mach F", "Baigent C", "Catapano AL", "Koskinas KC", "Casula M", "Badimon L", "Chapman MJ"],
        "ctt2010efficacy": ["Cholesterol Treatment Trialists' (CTT) Collaboration"], "hartz2006why": ["Hartz I", "Njølstad I", "Furu K", "Skurtveit S", "Eggen AE"]}
from shared_lipt import TFIX
def ref(k):
    r = REFS[k]
    if r["type"] == "web":
        if k == "web:kosis2026screening":
            return f"{r['authors']}. National health screening statistics: screening attendees by district (DT_35007_N098) and by sex and age group (DT_35007_N099), judgment results by disease (DT_35007_N105) and by sex and 5-year age group (DT_35007_N106), 2011-2024. Daejeon: Korean Statistical Information Service; {r['year']}. Accessed November 11, 2026. https://kosis.kr/statHtml/statHtml.do?orgId=350&tblId=DT_35007_N098, https://kosis.kr/statHtml/statHtml.do?orgId=350&tblId=DT_35007_N099, https://kosis.kr/statHtml/statHtml.do?orgId=350&tblId=DT_35007_N105 and https://kosis.kr/statHtml/statHtml.do?orgId=350&tblId=DT_35007_N106"
        return f"{r['authors']}. R: a language and environment for statistical computing. Version 4.6.0. Vienna: R Foundation for Statistical Computing; {r['year']}. Accessed October 20, 2026. {r['url']}"
    au = AUTH.get(k, r["authors"])
    a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:3]) + ", et al"
    t = TFIX.get(k, r["title"].rstrip(".")); t = t + ("" if t.endswith(("?", "!")) else ".")
    return f"{a}. {t} {r['journal']}. {r['year']};{r['vol']}:{r['pages']}."

class TX(JKMS):
    raw = False
    def __init__(self, cite="sup", lines=True, sz=SZ, header=True):
        super().__init__(cite); self.sz = sz; self._fsz = None
        st = self.doc.styles["Normal"]; st.font.size = Pt(sz); self.cell_ls = 2.0; self.title_pt = 11
        # US Letter, 1-inch margins; docDefaults single spacing (240) with after 0; 480 set explicitly only on body, abstract and reference paragraphs
        from docx.shared import Inches
        st.paragraph_format.line_spacing_rule = None; st.paragraph_format.line_spacing = None
        _dd = self.doc.styles.element.find(qn("w:docDefaults")); _pd = _dd.find(qn("w:pPrDefault")); _pp = _pd.find(qn("w:pPr")); _sp = _pp.find(qn("w:spacing"))
        if _sp is None: _sp = OxmlElement("w:spacing"); _pp.append(_sp)
        for _k, _v in (("w:after", "0"), ("w:line", "240"), ("w:lineRule", "auto")): _sp.set(qn(_k), _v)
        for s in self.doc.sections:
            s.page_width = Inches(8.5); s.page_height = Inches(11); s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)
        for s in self.doc.sections:
            if not lines:
                e = s._sectPr.find(qn("w:lnNumType"))
                if e is not None: s._sectPr.remove(e)
            fp = s.footer.paragraphs[0]
            for r in list(fp.runs): r._element.getparent().remove(r._element)   # Page numbers go in the header
            if header: self._header(s)
    def _header(self, s):   # Top left "Kim  running title", top right page number
        hp = s.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        _pp = hp._p.get_or_add_pPr(); _ps = _pp.find(qn("w:pStyle")); _pp.insert(0 if _ps is None else 1, OxmlElement("w:suppressLineNumbers"))   # Header paragraph (line-numbered document)
        w = s.page_width - s.left_margin - s.right_margin; ts = hp.paragraph_format.tab_stops
        from docx.shared import Inches
        ts.add_tab_stop(Inches(3.25), WD_TAB_ALIGNMENT.CLEAR)   # Clear the default centre tab of the Header style
        if abs(w - Inches(6.5)) > 1000: ts.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.CLEAR)
        ts.add_tab_stop(w, WD_TAB_ALIGNMENT.RIGHT)
        r = hp.add_run(f"{SURNAME}  {RUNNING}\t"); r.font.size = Pt(10); r.font.name = "Times New Roman"
        for kind in ("begin", "instr", "end"):
            r = hp.add_run(); r.font.size = Pt(10); r.font.name = "Times New Roman"
            if kind == "instr": it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"; r._element.append(it)
            else: fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); r._element.append(fc)
    def table(self, title, *a, **k):   # Table titles 11 pt bold, single spacing, 14 pt before
        from docx.enum.text import WD_LINE_SPACING
        n0 = len(self.doc.paragraphs); r = super().table(title, *a, **k); tp = self.doc.paragraphs[n0]
        for run in tp.runs: run.font.size = Pt(self.title_pt)
        tp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; tp.paragraph_format.space_before = Pt(14); tp.paragraph_format.space_after = Pt(4)
        return r
    def head(self, text, level=1):   # Main headings 14 pt, subheadings 12 pt bold, single spacing; sections 16 pt before; back-matter (level 4) and declaration (level 5) headings 24 before / 6 after
        sz, before, after = {1: (14, 16, 0), 2: (12, 6, 0), 3: (12, 4, 0), 4: (14, 24, 6), 5: (12, 24, 6)}[level]
        c = self.counting; self.counting = False; self._fsz = sz
        self.para(text, bold=level != 3, italic=level == 3, double=False, before=before, after=after)
        self._fsz = None; self.counting = c
    def save(self, path):   # With page numbers in the header the footer is empty -> remove footerReference and its relationship
        for s in self.doc.sections:
            for fr in s._sectPr.findall(qn("w:footerReference")):
                rid = fr.get(qn("r:id")); s._sectPr.remove(fr); self.doc.part.drop_rel(rid)
        super().save(path)
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if sz == 12: sz = self._fsz or self.sz
        if not self.raw:
            text = amer(text); text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)

def foot_row(J, text, sz=8, ls=None):   # Table footnotes 8 pt, single spacing (auto 240)
    from docx.enum.text import WD_LINE_SPACING
    p = J.doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; p.paragraph_format.space_before = Pt(3)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
SYM = "*†‡§"
def supmarks(header, rows, foot):
    """Replace footnote symbols (*, †, ‡, §) in a table with superscript a, b, c… in order of first appearance, in the footnote too (statistic names such as Gi* excluded)."""
    order = []
    for c in list(header) + [x for r in rows for x in r]:
        for ch in re.findall(r"(?<!Gi)[*†‡§]", str(c)):
            if ch not in order: order.append(ch)
    mp = {ch: "abcdefgh"[i] for i, ch in enumerate(order)}
    sub = lambda t: re.sub(r"(?<!Gi)[*†‡§]", lambda m: f"<sup>{mp[m.group(0)]}</sup>" if m.group(0) in mp else m.group(0), str(t))
    nf = sub(foot); assert not re.search(r"(?<!Gi)[*†‡§]", nf), ("symbol only in footnote", re.findall(r"(?<!Gi)[*†‡§]", nf))
    return [sub(h) for h in header], [[sub(x) for x in r] for r in rows], nf
def put_table(J, t, fs=9):
    h, rows, ft = supmarks(t[1], t[2], t[3])
    c = J.counting; J.counting = False; J.table_fit(amer(t[0]), [amer(x) for x in h], [[amer(x) for x in r] for r in rows], "", fs_max=fs, title_bold=True); foot_row(J, ft, 8); J.counting = c

# Tables 1 and 2 (values only from numbers_lipt)
from shared_lipt import TAB1_COV, GROUPS as _G, LABEL
GROUPS = [("Lifestyle-related risk factors" if g == "Lipid risk factors" else g, v) for g, v in _G]
def table1():
    from shared_lipt import SRCAB, YRAB, SRC_FOOT, UNIT
    T = N["T1"]; cols = ["W1_2011-17", "W2_2018-24", "2011-2024"]
    rows = [["__H__", "Health screening"],
            ["  District-years", "n", ""] + [f"{T[c]['n']:,}" for c in cols],
            ["  Attendances", "million", ""] + [f"{T[c]['exam']/1e6:.1f}" for c in cols],
            ["  Treated dyslipidaemia", "million", ""] + [f"{T[c]['cases']/1e6:.2f}" for c in cols],
            ["  Crude share treated", "% of attendances", ""] + [f"{T[c]['pos']:.1f}" for c in cols],
            ["  Crude rate", "per 100,000 attendances", ""] + [f"{N['s22'][k]['crude_per100k_228']:,.0f}" for k in ("2011-2017", "2018-2024", "2011-2024")],
            ["  Standardised rate, national", "per 100,000 attendances", ""] + [f"{N['s22'][k]['ASR_per100k_national_std2015']:,.0f}" for k in ("2011-2017", "2018-2024", "2011-2024")],
            ["  Treatment ratio, median*", "ratio", ""] + [f"{T[c]['sir_med']:.2f}" for c in cols],
            ["  Treatment ratio, P10–P90*", "ratio", ""] + [f"{T[c]['sir_p10']:.2f}–{T[c]['sir_p90']:.2f}" for c in cols]]
    for g, vs in GROUPS:
        rows.append(["__H__", f"{g}, mean (SD)"])
        for v in vs:
            mx = max(abs(T[c]['cov'][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
            rows.append([f"  {LABEL[v]}", UNIT[v], f"{SRCAB[v]}, {YRAB.get(v, '2011–24')}"] + [f"{T[c]['cov'][v][0]:,.{dp}f} ({T[c]['cov'][v][1]:,.{dp}f})" for c in cols])
    assert sum(1 for r in rows if r[0].startswith("  ") and r[2]) == 16
    _SF = SRC_FOOT.replace(" health screening statistics;", ";").replace(" national public sports facilities;", ";").replace(" basic livelihood security recipients.", ".")   # Shortened Table 1 footnote (avoids a page holding only footnotes)
    assert _SF != SRC_FOOT and _SF.count(";") == SRC_FOOT.count(";")
    foot = ("Treated dyslipidaemia, judged as diagnosed and on drug treatment; P10–P90, 10th–90th percentile; SD, standard deviation; respondents, Community Health Survey respondents; invited people, people invited to general health screening. "
            "Crude rate, treated attendances per 100,000 attendances; standardised rate, national rate directly standardised for sex and age to the 2015 national attendee structure (age- and sex-specific rates in Supplementary Table S11). "
            "Supplementary Table S3 gives medians, ranges and filled cells. "
            + _SF + " "
            "*Observed over expected numbers summed over the window (indirect standardisation by sex and 5-year age group). "
            "†Census years, interpolated between censuses and held at 2020 thereafter. "
            "‡Age-standardised district estimates. §Not surveyed in 2019 (obesity) or 2018 (moderate-to-vigorous activity); interpolated within districts.")
    return ("Table 1. Treated dyslipidaemia and 16 district covariates by window, Korea, 2011–2024", ["Characteristic", "Unit", "Source, years", "2011–2017", "2018–2024", "2011–2024"], rows, foot)
def table2():
    from shared_lipt import UNIT
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    f3 = lambda e, lo, hi: f"{e:.3f} ({lo:.3f}\u2060–\u2060{C.fh(hi)})"   # Line breaks only at the space between estimate and interval (word joiners around the dash inside the interval)
    t3 = lambda t: f"{t[0]:.3f} ({t[1]:.3f}\u2060–\u2060{C.fh(t[2]) if t[3] else f'{t[2]:.3f}'})"
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v)
            rows.append([f"  {LABEL[v]}" + ("†" if v == C.IMS else ""), f3(m['IRR'], m['lo'], m['hi']), f"{100*mv['cred_frac']:.0f}" if mv else "NA",
                         t3(N["epop"][v]), t3(N["sens_main"]["s8"][v]), t3(N["xf"]["E_crude"][v])])
    A = N["retention"]
    foot = (f"RR, rate ratio per 1 standard deviation of the covariate (units and standard deviations in Table 1); CrI, credible interval; NA, not applicable (forced into every specification). Principal model, negative binomial with a Besag–York–Mollié 2 district effect and random-walk and independent year effects, without a space–time interaction (n={N['n_rows']:,} district-years, {N['n_districts']} districts, 2011–2024), with expected numbers from national sex- and age-specific shares applied to attendees. "
            "The last 3 columns refit the principal model with other expected numbers: residents, the same shares applied to the resident population; age only, national age-specific shares without sex; crude, attendees multiplied by the national crude share, so that sex and age enter only through the forced sex ratio and share aged 80 years or older (post hoc). "
            "An association was regarded as credible when the 95% CrI excluded 1; RRs and CrIs are rounded to 3 decimals, and intervals with a bound shown as 1.000 were classified from unrounded values, which are reproduced by the analysis code in the repository. "
            f"The 3 credible covariates remained credible in {A[C.EDU]['kept']} (tertiary education), {A[C.IMS]['kept']} (specialists) and {A[C.MPA]['kept']} (activity) of {A[C.EDU]['n_specs']} alternative specifications; estimates from space–time interaction models are shown in Fig. 2 and Supplementary Table S5. "
            "The share aged 80 years or older is a forced control beyond indirect standardisation and is not interpreted. *Share of the 200 covariate-subset fits containing the covariate in which the CrI excluded 1 (subset-stable, at least 75% with the same sign in at least 95%). "
            "†Entered the models as log(1 + specialists per 100,000) before standardisation.")
    return ("Table 2. District characteristics and sex- and age-standardised treated dyslipidaemia in the principal model and with alternative expected numbers", ["Characteristic", "RR (95% CrI)", "Credible subsets, %*", "Residents", "Age only", "Crude"], rows, foot)
from shared_lipt import FIGCAP as _FC
FIGCAP = dict(_FC); _a = "the numbers on the right repeat each estimate."
assert _a in FIGCAP[2][1]
FIGCAP[2] = (FIGCAP[2][0], FIGCAP[2][1].replace(_a, "the numbers on the right repeat each estimate except those of the resident-denominator model, which are given in Table 2."))

def title_block(J, counts=None):   # Front matter single spacing; title 16 pt bold centred, authors 12 pt, affiliations and correspondence 9 pt centred
    def fp(text, sz, before=0, bold=False):
        p = J.para("", double=False, align="center", before=before); J._emit(p, text, sz, bold); return p
    fp(TITLE, 16, bold=True)
    fp(f"Running title: {RUNNING}", 11, before=6)
    fp(AUTHOR, 12, before=12)
    fp(AFFIL, 9, before=4)
    fp("<b>Corresponding author</b>", 9, before=12)
    fp(f"{AUTHOR}, {ADDRESS}. Telephone {PHONE}. Fax not available. E-mail {EMAIL}.", 9)
    fp(f"ORCID: Seongdae Kim https://orcid.org/{ORCID}", 9)
    fp("<b>Credits and grant information</b>", 9, before=12); fp(FUNDING, 9)
    fp("<b>Presentation</b>", 9, before=12); fp(PRESENTED, 9)
    if counts:
        fp("<b>Manuscript details</b>", 9, before=12)
        fp(f"Main text {counts['bw']:,} words; abstract {counts['aw']} words; {counts['nref']} references; 2 tables; 2 figures.", 9)
        fp("<b>Code availability</b>", 9, before=12)
        fp(f"GitHub {C.REPO_PH}; Zenodo https://doi.org/{C.ZEN_PH}", 9)

def build(counts=None):
    D = read_draft(); J = TX(cite="sup")
    title_block(J, counts)
    J.page_break(); J.head("Abstract", 1)
    for p, lab in zip(D["Abstract"], ABL):
        assert p.startswith(lab + ":"), (lab, p[:30]); J.para(f"<b>{lab}:</b> {p[len(lab)+1:].strip()}")
    J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Methods", 1)
    for i, (h, p) in enumerate(C.METHODS, 1): J.head(f"{i}. {h}", 2); J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for i, (h, p) in enumerate(C.RESULTS, 1): J.head(f"{i}. {h}", 2); J.para(pandoc_cites(p), indent=True)
    J.head("Discussion", 1); _k = 0   # Orphaned subheadings allowed (no keepNext or page breaks)
    for p in D["Discussion"]:
        if p.startswith("### "):
            _k += 1; J.head(f"{_k}. {p[4:].strip()}", 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.head("Conclusion", 1)
    for p in D["Conclusion"]: J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.raw = True; J.head("Acknowledgements", 4); J.raw = False; J.para(AI_STATEMENT)
    J.head("Author Contributions", 4); J.para(CONTRIB)
    J.head("Statements and Declarations", 4)
    for h, t in STATEMENTS: J.head(h, 5); J.para(t)
    J.head("Supplemental Material", 4)
    J.para("Supplementary Sections S1–S9, Supplementary Tables S1–S11 and Supplementary Figs. S1 and S2 are provided in a separate file, and the completed STROBE checklist is provided as a separate file.")
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k_ in enumerate(J.cites, 1): s_ = f"{i}. " + ref(k_); rl.append(s_); J.para(s_)
    J.raw = False
    # Table 1 at 8 pt: at 9 pt the source/unit cells wrap and leave a group label at the page end
    J.title_pt = 11; J.page_break(); put_table(J, table1(), fs=8); J.page_break(); J.fit_pad = 0.45; put_table(J, table2(), fs=9); J.fit_pad = 0.65; J.title_pt = None
    J.page_break(); J.head("Figure Legends", 1)
    for k_ in sorted(FIGCAP):
        p_ = J.para("", double=False, before=10, after=3); J._emit(p_, f"<b>Fig. {k_}. {FIGCAP[k_][0]}</b>", 11); J._emit(p_, f" {FIGCAP[k_][1]}", 10)
    return J, rl, D
def titlepage(counts):
    J = TX(cite="sup", lines=False); title_block(J, counts); return J
def to_pdf(path):
    subprocess.run([SOFFICE, "--headless", "-env:UserInstallation=file://" + tempfile.mkdtemp(prefix="lo_lipt_"), "--convert-to", "pdf", "--outdir", OUT, path], capture_output=True, check=True)
def npages(pdf): return int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
def docx_bw(path):
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    a = t.find("\nIntroduction\n"); return len(t[a:t.find("\nAcknowledgements\n", a)].split())
def abstract_words(D):
    AB = [re.sub(r"^(Objective|Methods|Results|Conclusion):\s*", "", x) for x in D["Abstract"]]; return sum(len(x.split()) for x in AB) + 4
if __name__ == "__main__":
    p = os.path.join(OUT, MSF); D = read_draft(); aw = abstract_words(D)
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p)
    counts = {"bw": bw, "aw": aw, "nref": len(KEYS)}
    J, rl, D = build(counts); J.doc_title = "Manuscript"; J.save(p); assert docx_bw(p) == bw
    to_pdf(p); np_ = npages(p[:-5] + ".pdf")
    TP = titlepage(counts); tp = os.path.join(OUT, TPF); TP.doc_title = "Title Page"; TP.save(tp)
    open(os.path.join(OUT, os.environ.get("LIPT_WORDCOUNT") or "wordcount.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=2\ntitle_words={len(TITLE.split())}\npages={np_}\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | pages {np_} | title words {len(TITLE.split())}")
